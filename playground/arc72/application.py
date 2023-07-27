import beaker
import pyteal as pt
from beaker import consts
from beaker.lib import storage
from typing import Literal

Bytes256 = pt.abi.StaticBytes[Literal[256]]

INDEX = 0
MAX_TOKENS = pt.Int(10)
ZERO_ADDRESS =  pt.Global.zero_address()
APPROVAL = False
URL = "https://github.com/algorandfoundation/ARCs"
URL = URL + (256-len(URL))*" "
URL = pt.Bytes(URL)
class Token(pt.abi.NamedTuple):
    owner: pt.abi.Field[pt.abi.Address]
    uri: pt.abi.Field[Bytes256]
    controller: pt.abi.Field[pt.abi.Address]

class Control(pt.abi.NamedTuple):
    owner: pt.abi.Field[pt.abi.Address]
    controller: pt.abi.Field[pt.abi.Address]

class Arc72:
    # tokenList = storage.BoxList(pt.abi.Address, MAX_TOKENS)
    index =  beaker.GlobalStateValue(
        stack_type=pt.TealType.uint64,
        descr="index of token",
        static=False,
    )
    token_box = storage.BoxMapping(pt.abi.Uint64, Token)
    control_box = storage.BoxMapping(Control, pt.abi.Bool)
    # declared_local_value = beaker.LocalStateValue(
    #     stack_type=pt.TealType.uint64,
    #     default=pt.Int(1),
    #     descr="An int stored for each account that opts in",
    # )

app = beaker.Application("ARC72", state=Arc72())

@app.external(read_only=True)
def arc72_ownerOf(tokenId: pt.abi.Uint64, *, output: pt.abi.Address) -> pt.Expr:
    return pt.Seq(
        app.state.token_box[tokenId].store_into(t := Token()),
        t[0].store_into(output)
    )
@app.external(read_only=True)
def arc72_tokenURI(tokenId: pt.abi.Uint64, *, output: Bytes256) -> pt.Expr:
    return pt.Seq(
        app.state.token_box[tokenId].store_into(t := Token()),
        t[1].store_into(output)
    )


# def _events(methodName: pt.abi.String, arguments: pt.abi.String):
#     return pt.MethodSignature()




@app.external
def transferTo(to: pt.abi.Address, tokenId: pt.abi.Uint64):
    return pt.Seq(
        (t := Token()).decode(app.state.token_box[tokenId].get()),
        (o := pt.abi.Address()).set(to),
        (u := pt.abi.make(Bytes256)).set(t.uri),     
        (c := pt.abi.Address()).set(t.controller),        
        t.set(o,u,c),
        app.state.token_box[tokenId].set(t)
    )  

@app.external
def arc72_transferFrom(_from: pt.abi.Address, to: pt.abi.Address, tokenId: pt.abi.Uint64):
    pt.MethodSignature("arc72_Transfer(address,address,uint64)")
    return pt.Seq(
        (t := Token()).decode(app.state.token_box[tokenId].get()),
        (c := pt.abi.Address()).set(t.controller),   
        (o := pt.abi.Address()).set(t.owner),    
        (operator := pt.abi.Address()).set(pt.Txn.sender()),  
        (key := Control()).set(operator, _from),
        pt.If( pt.Or(
                    pt.Eq(pt.Txn.sender(), _from.get()),
                    pt.Eq(c.get(), pt.Txn.sender()),
                )).Then( 
        transferTo(to, tokenId) 
        ).Else(
            pt.Assert(app.state.control_box[key].exists()),
            transferTo(to, tokenId) 
        ),
    )  


    

@app.external
def arc72_approve(approved: pt.abi.Address, tokenId: pt.abi.Uint64): #TODO
    pt.MethodSignature("arc72_Approval(address,address,uint64)")

    return pt.Seq(
    (t := Token()).decode(app.state.token_box[tokenId].get()),
    (o := pt.abi.Address()).set(t.owner),
    (u := pt.abi.make(Bytes256)).set(t.uri),
    (c := pt.abi.Address()).set(approved),
    t.set(o,u,c),
    pt.Assert(pt.Eq(pt.Txn.sender(), o.get())),
        app.state.token_box[tokenId].set(t)
        )

@app.external
def arc72_setApprovalForAll(operator: pt.abi.Address, *, output: pt.abi.Bool): #TODO
    pt.MethodSignature("arc72_ApprovalForAll(address,address,bool)")

    return pt.Seq(
        (f := pt.abi.Address()).set(pt.Txn.sender()),
        (key := Control()).set(operator, f),
        (exist := pt.abi.Bool()).set(app.state.control_box[key].exists()),
        (b := pt.abi.Bool()).set(pt.Int(1)),
        pt.If(exist.get()).Then(     
                
                pt.Pop(app.state.control_box[key].delete()),
                output.set(pt.Int(0)),
            
        ).Else(
                app.state.control_box[key].set(b),        
                output.set(pt.Int(1)),
            )
        )
    

@app.external
def mint(to: pt.abi.Address):
    return pt.Seq(
        pt.Assert(app.state.index.get() < MAX_TOKENS),
        (i := pt.abi.Uint64()).set(app.state.index),
        (o := pt.abi.Address()).set(to.get()),
        (u := pt.abi.make(Bytes256)).set(URL),
        (c := pt.abi.Address()).set(ZERO_ADDRESS),
        (t := Token()).set(o, u, c),
        app.state.token_box[i].set(t),
        transferTo(o, i),
        app.state.index.set(i.get() + pt.Int(1)),
    )  

@app.external(read_only=True)
def arc72_totalSupply(*, output: pt.abi.Uint64):
    return output.set(app.state.index.get())
    
@app.external(read_only=True)
def arc72_tokenByIndex(index: pt.abi.Uint64, *, output: pt.abi.Uint64):
    return output.set(index.get())

def compute_min_balance(members: int):
    """Compute the min balance for the app to hold the boxes we need"""
    return (
        consts.ASSET_MIN_BALANCE  # Cover min bal for member token
        + (
            consts.BOX_FLAT_MIN_BALANCE
            + (pt.abi.size_of(pt.abi.Uint64) * consts.BOX_BYTE_MIN_BALANCE)
        )
        * members  # cover min bal for balance boxes we might create
        + (
            consts.BOX_FLAT_MIN_BALANCE
            + (members * pt.abi.size_of(pt.abi.Address) * consts.BOX_BYTE_MIN_BALANCE)
        )  # cover min bal for member list box
    )

@app.opt_in
def opt_in() -> pt.Expr:
    return app.initialize_local_state()

