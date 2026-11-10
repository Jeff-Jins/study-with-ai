"""TLS 연결을 열고 협상 결과와 서버 인증서를 출력한다.

사용법: python3 tls_client.py [호스트] [포트]
예:     python3 tls_client.py example.com 443
"""
import socket
import ssl
import sys

host = sys.argv[1] if len(sys.argv) > 1 else "example.com"
port = int(sys.argv[2]) if len(sys.argv) > 2 else 443

# 시스템의 신뢰 CA 목록을 쓰고, 인증서 검증 + 호스트 이름 확인을 켠다.
ctx = ssl.create_default_context()

with socket.create_connection((host, port), timeout=10) as raw:
    # server_hostname → ClientHello의 SNI, 그리고 인증서 이름 검증에 쓰인다.
    with ctx.wrap_socket(raw, server_hostname=host) as tls:
        print("버전     :", tls.version())
        print("암호군   :", tls.cipher()[0])
        cert = tls.getpeercert()
        print("주체     :", dict(x[0] for x in cert["subject"]))
        print("발급자   :", dict(x[0] for x in cert["issuer"]))
        print("유효기간 :", cert["notBefore"], "~", cert["notAfter"])
        print("SAN      :", [v for k, v in cert.get("subjectAltName", ()) if k == "DNS"])

        # TODO(직접 해보기): 아래 주석을 풀고 HTTP 요청을 TLS 위로 보내 보자.
        # tls.sendall(f"HEAD / HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode())
        # print(tls.recv(4096).decode(errors="replace"))
