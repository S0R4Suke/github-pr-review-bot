# HMAC認証
import hmac, hashlib

def checkHMAC(event, SECRET):
    signature = event["headers"].get("X-Hub-Signature", "")
    
    signed_body = (
        "sha1="
        + hmac.new(
            bytes(SECRET, "utf-8"),
            bytes(event["body"], "utf-8"),
            hashlib.sha1
        ).hexdigest()
    )
    
    # タイミング攻撃対策
    return hmac.compare_digest(signature, signed_body)
