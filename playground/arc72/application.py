import beaker
import pyteal as pt
from beaker import consts
from beaker.lib import storage
from typing import Literal

INDEX = 0
MAX_TOKENS = 10
ZERO_ADDRESS =  pt.GlobalField.zero_address
APPROVAL = False

class Token(pt.abi.NamedTuple):
    owner: pt.abi.Field[pt.abi.Address]
    uri: pt.abi.Field[pt.abi.StaticBytes[Literal[32]]]
    controller: pt.abi.Field[pt.abi.Address]

class Arc72:
    # tokenList = storage.BoxList(pt.abi.Address, MAX_TOKENS)
    index =  beaker.GlobalStateValue(
        stack_type=pt.TealType.uint64,
        descr="index of token",
        static=False,
    )
    token_box = storage.BoxMapping(pt.abi.Uint64, Token)

    ownerApproval = storage.BoxMapping(pt.abi.Uint64, pt.abi.Address)

app = beaker.Application("ARC72", state=Arc72())

@app.external(read_only=True)
def arc72_ownerOf(tokenId: pt.abi.Uint64, *, output: pt.abi.Address) -> pt.Expr:
    return pt.Seq(
        app.state.token_box[tokenId].store_into(t := Token()),
        t[0].store_into(output)
    )
@app.external(read_only=True)
def arc72_tokenURI(tokenId: pt.abi.Uint64, *, output: pt.abi.StaticBytes[Literal[32]]) -> pt.Expr:
    return pt.Seq(
        app.state.token_box[tokenId].store_into(t := Token()),
        t[1].store_into(output)
    )

def _events(methodName: pt.abi.String, arguments: pt.abi.String):
    return pt.Log(pt.MethodSignature(pt.Concat(methodName,"(",arguments,")")))

@app.external
def arc72_transferTo(recipient: pt.abi.Address, tokenId: pt.abi.Uint64):
    return pt.Seq(
        (t := Token()).decode(app.state.token_box[tokenId].get()),
        (o := pt.abi.Address()).set(recipient),
        (u := pt.abi.StaticBytes[Literal[32]]()).set(t.uri),     
        (c := pt.abi.Address()).set(t.controller),        
        t.set(o,u,c),
        app.state.token_box[tokenId].set(t)
    )  

# @app.external
# def arc72_transferFrom(sender: pt.abi.Address, recipient: pt.abi.Address, tokenId: pt.abi.Uint64):
#     return pt.Seq(
#             pt.Assert(
#                 pt.Or(
#                     pt.abi.eq(pt.Txn.sender(), sender),
#                     pt.abi.eq(pt.BoxGet(tokenId)[2], pt.Txn.sender()),
#                     app.state.ownerApproval[pt.Txn.sender()].exists()
#                 )
#             ),
#         _events("arc72_Transfer",
#                     pt.Concat(pt.Bytes(sender),
#                     pt.Bytes(recipient),
#                     pt.Bytes(tokenId)
#                     )
#         ),
#         arc72_transferTo(recipient, tokenId)
#     )
        


    # @app.external
    # def arc72_approve(self, approved: pt.abi.Address, tokenId: pt.abi.Uint64):
    #     return pt.Seq(
    #         (i := pt.abi.Uint64()).set(tokenId),
    #         (o := pt.abi.Address()).set(self.pt.BoxGet(tokenId)[0]),
    #         (u := pt.abi.String()).set(self.pt.BoxGet(tokenId)[1]),
    #         (c := pt.abi.Address()).set(approved),
    #         (t := Token()).set(o, u, c),
    #         self.box[i].set(t),
    #         self.events(
    #             "arc72_Approval",
    #             pt.Concat(
    #                 pt.Bytes(o),
    #                 pt.Bytes(approved),
    #                 pt.Bytes(tokenId)
    #             )
    #         ),
    #     )  

    # @app.external
    # def arc72_setApprovalForAll(self, operator: pt.abi.Address, approved: pt.abi.Bool):
    #     return pt.If(approved).Then(
    #         pt.Seq(
    #             self.ownerApproval.set(operator),
    #             self._events(
    #                 "arc72_ApprovalForAll",
    #                 pt.Concat(
    #                     pt.Bytes(operator),
    #                     pt.Bytes("True"),
    #                 )
    #             ),
    #         )
    #     ).ElseIf(
    #         pt.Seq(
    #             self.ownerApproval[operator].delete(),
    #             self.events(
    #                 "arc72_ApprovalForAll",
    #                 pt.Concat(
    #                     pt.Bytes(operator),
    #                     pt.Bytes("False"),
    #                 )
    #             )
    #         )
    #     )

    # @app.external
    # def mint(self, recipient: pt.abi.Address, uri: pt.abi.String):
    #     return pt.Seq(
    #         pt.Assert(self.index.get() < MAX_TOKENS),
    #         (i := pt.abi.Uint64()).set(self.index.get()),
    #         (o := pt.abi.Address()).set(recipient),
    #         (u := pt.abi.String()).set(uri),
    #         (c := pt.abi.Address()).set(ZERO_ADDRESS),
    #         (t := Token()).set(o, u, c),
    #         self.box[i].set(t),
    #         self._events("arc72_Transfer",
    #                     pt.Concat(pt.Bytes(ZERO_ADDRESS),
    #                     pt.Bytes(recipient),
    #                     pt.Bytes(i)
    #             )
    #         ),
    #         self.index.set(i + 1),
    #     )  

    # @app.external(read_only=True)
    # def arc72_totalSupply(self):
    #     return self.index.get()
    
    # @app.external(read_only=True)
    # def arc72_tokenByIndex(self, index: pt.abi.Uint64):
    #     return index
