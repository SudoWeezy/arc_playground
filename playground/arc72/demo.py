from algokit_utils import LogicError
import application
from beaker import client, localnet, consts, localnet
from algosdk import encoding, abi
import pyteal as pt
import base64
def abi_encode(abi_type, value):
    record_codec = abi.ABIType.from_string(str(abi_type.type_spec()))
    return record_codec.encode(value)

def abi_decode(abi_type, value):
    record_codec = abi.ABIType.from_string(str(abi_type.type_spec()))
    return record_codec.decode(value)

def main() -> None:
    accts = localnet.get_accounts()
    acct = accts.pop() #46FSPYUMSTZ3RVEAGI4WSC6ZGGHBB6FWL3M4DEL3PBPDVQTPVNSTTLYMGM
    member = accts.pop() #WMXNIS3IC2JDEILZ4KAUVUBYDT6ABNDPPWQQT4X77NZDXTNFMY5EY3RJ4E
    admin = accts.pop() #PHOJ23RY4NIS6KYVFUXQIRWI5PIZSP2GVWWXUJOCALZBNUAYVY2HL7YFBQ


    print(acct.address)
    print(member.address)
    print(admin.address)
    algod_client = localnet.get_algod_client()
    app_client = client.ApplicationClient(
        algod_client, application.app, signer=acct.signer
    )

    max_nft = 10
    # create the app
    app_id, app_address, _ = app_client.create()
    print(f"Deployed Application ID: {app_id} Address: {app_address}")

    app_client_m = client.ApplicationClient(
        algod_client, application.app, app_id=app_id, signer=member.signer
    )
    app_client_a = client.ApplicationClient(
        algod_client, application.app, app_id=app_id, signer=admin.signer
    )

    # fund the app with enough to cover the min balance for the boxes we need
    # plus some extra to cover any boxes created with `fill_box`
    min_balance = application.compute_min_balance(max_nft) * 2
    app_client.fund(min_balance)

    # mint an nft for the user 
    app_client.call(application.mint, to=acct.address, boxes=[(0, 0)])

    arc72_ownerOf = app_client.call(application.arc72_ownerOf, tokenId=0, boxes=[(0, 0)])
    print(arc72_ownerOf.return_value)

    arc72_tokenURI = app_client.call(application.arc72_tokenURI, tokenId=0, boxes=[(0, 0)])
    print(bytearray(arc72_tokenURI.return_value).decode('utf-8').replace(" ",""))
        
    control = abi_encode(application.Control(), (admin.address,member.address))

    arc72_transferFrom = app_client.call(
        application.arc72_transferFrom,
        _from=acct.address,
        to=member.address,
        tokenId=0,
        boxes=[[0, 0],[0, control]]
        )

    arc72_ownerOf = app_client.call(application.arc72_ownerOf, tokenId=0, boxes=[(0, 0)])
    print(arc72_ownerOf.return_value) 

    res=app_client_m.call(
        application.arc72_setApprovalForAll, 
        operator=admin.address,
        boxes=[[0, control]],
        sender=member.address,
        )
    app_client_a.call(
        application.arc72_transferFrom,
        _from=member.address,
        to=acct.address,
        tokenId=0,
        boxes=[[0, 0],[0, control]],
        sender=admin.address
        )
    arc72_ownerOf = app_client.call(application.arc72_ownerOf, tokenId=0, boxes=[(0, 0)])
    print(arc72_ownerOf.return_value) 
    res=app_client_m.call(
        application.arc72_setApprovalForAll, 
        operator=admin.address,
        boxes=[[0, control]],
        sender=member.address,
        )
    res=app_client.call(
        application.arc72_approve, 
        approved=admin.address,
        tokenId=0,
        boxes=[[0, 0]],
        )
    control = abi_encode(application.Control(), (admin.address,acct.address))
    token = abi_encode(pt.abi.Uint64(), 0)

    for box in app_client.client.application_boxes(app_client.app_id)["boxes"]:
        name = base64.b64decode(box["name"])
        if name == control:
            contents = app_client.client.application_box_by_name(app_client.app_id, name)
            box_key = abi_decode(application.Control(), name)
            print(f"Current Box: {box_key} ")
        if name == token:
            contents = app_client.client.application_box_by_name(app_client.app_id, name)
            print(contents)
            contents = abi_decode(application.Token(), base64.b64decode(contents["value"]))
            box_key = abi_decode(pt.abi.Uint64(), name)
            print(f"Current Box: {box_key} {contents}")
 
    app_client_a.call(
        application.arc72_transferFrom,
        _from=acct.address,
        to=member.address,
        tokenId=0,
        boxes=[[0, 0],[0, control]],
        sender=admin.address
        )
    arc72_ownerOf = app_client.call(application.arc72_ownerOf, tokenId=0, boxes=[(0, 0)])
    print(arc72_ownerOf.return_value) 
    for box in app_client.client.application_boxes(app_client.app_id)["boxes"]:
        name = base64.b64decode(box["name"])
        if name == control:
            contents = app_client.client.application_box_by_name(app_client.app_id, name)
            box_key = abi_decode(application.Control(), name)
            print(f"Current Box: {box_key} ")



if __name__ == "__main__":
    main()
