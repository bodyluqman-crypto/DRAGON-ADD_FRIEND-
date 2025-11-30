from flask import Flask, jsonify, request
import requests
import mymessage_pb2
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import random
import binascii
from concurrent.futures import ThreadPoolExecutor
import os
import time

app = Flask(__name__)

# إعدادات التشفير الحقيقية
AES_KEY = b'Yg&tc%DEuh6%Zc^8'
AES_IV = b'6oyZDr22E3ychjM%'

# تخزين المستخدمين
users = {}
request_logs = []

# دالة التشفير
def encrypt_message(key, iv, plaintext):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_message = pad(plaintext, AES.block_size)
    encrypted_message = cipher.encrypt(padded_message)
    return encrypted_message

# جلب توكنات حقيقية لـ OB51
def fetch_tokens():
    token_url = "https://jwt-gen-api-v2.onrender.com/token?uid=4016344983&password=D61AF8D47D5A22D322658C6DD4DE33B929A277C915BCF9DDBF7CBD2488769A02"
    try:
        response = requests.get(token_url, timeout=10)
        if response.status_code == 200:
            tokens_data = response.json()
            if tokens_data and len(tokens_data) > 0:
                tokens = tokens_data[0]['token']
                return tokens
        return []
    except Exception as e:
        print(f"Error fetching tokens: {e}")
        return []

# إرسال طلب إضافة - OB51
def send_add_request(token, hex_encrypted_data):
    url = "https://clientbp.ggblueshark.com/RequestAddingFriend"
    payload = bytes.fromhex(hex_encrypted_data)
    headers = {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/octet-stream",
        'Expect': "100-continue",
        'Authorization': f"Bearer {token}",
        'X-Unity-Version': "2021.3.34f1",  # Updated for OB51
        'X-GA': "v1 1",
        'ReleaseVersion': "OB51"  # OB51
    }

    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        return response.status_code, response.text
    except Exception as e:
        return 500, str(e)

# إزالة صديق - OB51
def send_remove_request(token, hex_encrypted_data):
    url = "https://clientbp.common.ggbluefox.com/RemoveFriend"
    payload = bytes.fromhex(hex_encrypted_data)
    headers = {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/octet-stream",
        'Expect': "100-continue",
        'Authorization': f"Bearer {token}",
        'X-Unity-Version': "2021.3.34f1",  # Updated for OB51
        'X-GA': "v1 1",
        'ReleaseVersion': "OB51"  # OB51
    }

    try:
        response = requests.post(url, data=payload, headers=headers, verify=False, timeout=10)
        return response.status_code, response.text
    except Exception as e:
        return 500, str(e)

# إنشاء Protobuf message
def create_protobuf_message(uid, operation_type=22):
    message = mymessage_pb2.MyMessage()
    message.field1 = 9797549324  # Your ID
    message.field2 = int(uid)    # Target UID
    message.field3 = operation_type  # Operation type
    return message.SerializeToString()

# الصفحة الرئيسية
@app.route('/')
def home():
    return jsonify({
        "message": "🐉 Dragon FF API - OB51 Real",
        "version": "OB51",
        "developer": "DRAGON",
        "endpoints": {
            "/": "API Information",
            "/add/<uid>": "Add friend by UID",
            "/remove/<uid>": "Remove friend by UID", 
            "/list": "List added users",
            "/stats": "API statistics",
            "/health": "Health check"
        }
    })

# إضافة صديق
@app.route('/add/<uid>', methods=['GET'])
def add_friend(uid):
    try:
        # التحقق من UID
        if not uid.isdigit():
            return jsonify({"error": "Invalid UID"}), 400

        # جلب اسم اللاعب
        player_name = "Unknown"
        try:
            player_info_url = f"https://ff.garena.com/api/player/{uid}"
            response = requests.get(player_info_url, timeout=5)
            if response.status_code == 200:
                player_data = response.json()
                player_name = player_data.get('username', 'Unknown')
        except:
            pass

        # إنشاء الرسالة
        serialized_message = create_protobuf_message(uid, 22)
        encrypted_data = encrypt_message(AES_KEY, AES_IV, serialized_message)
        hex_encrypted_data = binascii.hexlify(encrypted_data).decode('utf-8')

        # جلب التوكن وإرسال الطلب
        token = fetch_tokens()
        if not token:
            return jsonify({"error": "No tokens available"}), 500

        status_code, response_text = send_add_request(token, hex_encrypted_data)

        # تسجيل النتيجة
        log_entry = {
            "timestamp": time.time(),
            "operation": "ADD",
            "uid": uid,
            "player_name": player_name,
            "status_code": status_code,
            "success": status_code == 200
        }
        request_logs.append(log_entry)

        if status_code == 200:
            users[uid] = {
                "uid": uid,
                "player_name": player_name,
                "added_at": time.time()
            }
            return jsonify({
                "success": True,
                "message": f"Friend request sent to {player_name}",
                "uid": uid,
                "player_name": player_name
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Failed to send request. Status: {status_code}",
                "response": response_text
            }), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# إزالة صديق
@app.route('/remove/<uid>', methods=['GET'])
def remove_friend(uid):
    try:
        if not uid.isdigit():
            return jsonify({"error": "Invalid UID"}), 400

        # إنشاء الرسالة
        serialized_message = create_protobuf_message(uid, 22)
        encrypted_data = encrypt_message(AES_KEY, AES_IV, serialized_message)
        hex_encrypted_data = binascii.hexlify(encrypted_data).decode('utf-8')

        # جلب التوكن وإرسال الطلب
        token = fetch_tokens()
        if not token:
            return jsonify({"error": "No tokens available"}), 500

        status_code, response_text = send_remove_request(token, hex_encrypted_data)

        # تسجيل النتيجة
        log_entry = {
            "timestamp": time.time(),
            "operation": "REMOVE", 
            "uid": uid,
            "status_code": status_code,
            "success": status_code == 200
        }
        request_logs.append(log_entry)

        if status_code == 200:
            if uid in users:
                del users[uid]
            return jsonify({
                "success": True,
                "message": f"User {uid} removed successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Failed to remove user. Status: {status_code}",
                "response": response_text
            }), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# عرض المستخدمين المضافين
@app.route('/list', methods=['GET'])
def list_users():
    return jsonify({
        "total_users": len(users),
        "users": users
    })

# إحصائيات API
@app.route('/stats', methods=['GET'])
def stats():
    successful_requests = len([log for log in request_logs if log['success']])
    failed_requests = len([log for log in request_logs if not log['success']])
    
    return jsonify({
        "total_requests": len(request_logs),
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "total_users": len(users),
        "version": "OB51"
    })

# فحص الحالة
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "version": "OB51",
        "timestamp": time.time(),
        "server": "Vercel"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
