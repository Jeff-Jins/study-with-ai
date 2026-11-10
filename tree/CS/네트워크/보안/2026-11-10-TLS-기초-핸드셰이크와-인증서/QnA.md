# 질문과 답 — TLS 기초 - 핸드셰이크와 인증서

> 노트: [README.md](README.md)

### Q. AEAD 암호가 뭐야?
- 날짜: 2026-11-10
- 답: **AEAD = Authenticated Encryption with Associated Data.** 암호화(기밀성)와 변조 검사(무결성)를 **한 번의 연산으로 같이** 해 주는 암호 방식이다.
  - **암호화할 때** 넣는 것: 키, nonce(매번 달라야 하는 값), 평문, 그리고 *associated data*(암호화는 안 하지만 변조는 막고 싶은 데이터). 나오는 것: 암호문 + **인증 태그**(짧은 체크값).
  - **복호화할 때**: 태그가 맞지 않으면 평문을 아예 돌려주지 않고 실패한다. 한 비트만 바뀌어도 들킨다.
  - **TLS 1.3에서는** 레코드 헤더(타입, 버전, 길이)가 associated data로 들어간다. 그래서 헤더는 평문으로 보이지만 바꿀 수 없다.
  - **왜 따로 하지 않나**: TLS 1.2 이전에는 "CBC 암호화 + HMAC"을 따로 조합했다. 조합 순서(MAC-then-encrypt) 때문에 패딩 오라클 같은 공격(Lucky Thirteen 등)이 계속 나왔다. AEAD는 둘을 하나로 묶어 그런 실수를 없앤다. **TLS 1.3은 AEAD 암호군만 허용한다.**
  - **실습에서 본 예**: `Ciphersuite: TLS_AES_256_GCM_SHA384` → 레코드 암호화는 AEAD인 **AES-256-GCM**이 맡는다. 뒤의 `SHA384`는 MAC이 아니라 핸드셰이크 키 파생(HKDF)용 해시다.
  - **주의점**: 같은 키로 같은 nonce를 두 번 쓰면(특히 GCM) 보안이 무너진다. TLS 1.3은 레코드마다 순번(sequence number)을 IV에 XOR해서 nonce가 겹치지 않게 한다.
- 대표 AEAD: AES-GCM, ChaCha20-Poly1305, AES-CCM
- 더 보기: README의 [개념 설명 > 왜 필요한가](README.md#왜-필요한가) 표의 "무결성" 줄, [RFC 8446](https://www.rfc-editor.org/rfc/rfc8446) 5.2절 Record Payload Protection

### Q. RFC 8446은 프로토콜이지?
- 날짜: 2026-11-10
- 답: 정확히는 **프로토콜을 정의한 문서(명세서)**다. 프로토콜 자체는 **TLS 1.3**이고, RFC 8446은 "TLS 1.3은 이렇게 동작해야 한다"를 적어 둔 표준 문서다.
  - **RFC**(Request for Comments)는 인터넷 표준을 만드는 IETF가 발행하는 번호 붙은 문서 시리즈다. 예: RFC 9293 = TCP, RFC 9110 = HTTP 의미론.
  - 비유하면 **프로토콜 = 게임 규칙**, **RFC = 규칙서 책**이다. OpenSSL, 브라우저 같은 구현체는 이 규칙서를 보고 만든다.
  - 규칙서는 개정될 수 있다. RFC 8446(2018)은 2026년 7월 **RFC 9846**으로 대체됐지만, 프로토콜 이름과 버전은 그대로 TLS 1.3이고 하위 호환된다.
  - 그래서 "TLS 1.3을 쓴다"가 맞는 표현이고, "RFC 8446을 쓴다"는 "RFC 8446에 정의된 TLS 1.3을 쓴다"는 뜻이다.
- 더 보기: [RFC 8446 상태 페이지](https://datatracker.ietf.org/doc/rfc8446/) ("Obsoleted by RFC 9846" 표시), [RFC 9846](https://datatracker.ietf.org/doc/rfc9846/)

### Q. SNI는 뭐야?
- 날짜: 2026-11-10
- 답: **SNI = Server Name Indication.** 클라이언트가 ClientHello에 "나는 **example.com**에 접속하려고 해"라고 도메인 이름을 적어 보내는 TLS 확장이다.
  - **왜 필요한가**: 서버 한 대(IP 하나)에 도메인 수백 개가 함께 올라가는 경우가 흔하다(가상 호스팅, CDN). 서버는 핸드셰이크 도중에 **어떤 도메인의 인증서**를 보낼지 정해야 한다. 그런데 HTTP의 `Host` 헤더는 핸드셰이크가 끝난 *뒤에* 암호화돼서 오기 때문에 너무 늦다. 그래서 핸드셰이크 맨 앞인 ClientHello에 이름을 실어 보낸다.
  - **직접 확인한 것**: 같은 IP(`104.20.23.154`)에 SNI만 바꿔서 붙었더니 서버가 다른 인증서를 줬다.
    ```
    $ openssl s_client -connect 104.20.23.154:443 -servername example.com        → subject=CN=example.com
    $ openssl s_client -connect 104.20.23.154:443 -servername www.cloudflare.com → subject=CN=www.cloudflare.com
    $ openssl s_client -connect 104.20.23.154:443 -noservername                   → alert handshake failure
    ```
    SNI가 없으면 서버가 어떤 인증서를 줄지 몰라서 핸드셰이크를 거부했다.
  - **코드에서는**: `lab/tls_client.py`의 `wrap_socket(raw, server_hostname=host)`가 SNI를 넣는다. 이 값은 인증서의 SAN과 맞는지 검증하는 데에도 쓰인다.
  - **한계(프라이버시)**: ClientHello는 평문이라서 네트워크 중간에서 "이 사람이 어느 사이트에 가는지"가 SNI로 보인다. 내용은 암호화돼도 목적지 도메인은 드러나는 것이다. 이를 숨기려는 후속 기술이 **ECH(Encrypted Client Hello)**다.
- 더 보기: README [개념 설명 > 어떻게 동작하나](README.md#어떻게-동작하나--tls-13-핸드셰이크-1-rtt)의 ClientHello 설명

### Q. DHE는 뭐야?
- 날짜: 2026-11-10
- 답: **DHE = Diffie-Hellman Ephemeral.** 서로 비밀을 한 번도 보낸 적 없는 두 사람이, **공개된 값만 주고받아서** 같은 비밀키를 만들어 내는 방법(Diffie-Hellman 키 교환)이다. 여기에 **연결할 때마다 새 키를 쓰고 버린다(ephemeral, 일회용)**는 조건이 붙은 것이 DHE다.
  - **원리 (작은 숫자로)**: 모두가 아는 값 `p=23, g=5`
    ```
    클라이언트: 비밀 a=6  → 공개 A = 5^6  mod 23 = 8   ──보냄──▶
    서버:       비밀 b=15 → 공개 B = 5^15 mod 23 = 19  ◀──보냄──
    클라이언트: B^a mod 23 = 19^6  mod 23 = 2
    서버:       A^b mod 23 = 8^15  mod 23 = 2   → 둘 다 2! (공유 비밀)
    ```
    도청자는 `23, 5, 8, 19`를 다 보지만, 여기서 a나 b를 알아내는 문제(이산 로그)가 실제 크기의 숫자에서는 사실상 풀 수 없을 만큼 어렵다.
  - **ECDHE**: 같은 아이디어를 타원곡선 위에서 하는 버전이다. 키가 짧고 빨라서 요즘은 대부분 이것을 쓴다. 실습에서 본 `X25519`가 ECDHE 그룹이고, `X25519MLKEM768`은 여기에 양자내성 알고리즘을 섞은 하이브리드다.
  - **TLS 1.3에서의 위치**: ClientHello/ServerHello의 `key_share`가 바로 위의 공개값(A, B)이다. 둘 다 받으면 공유 비밀이 생기고, 여기서 HKDF로 암호화 키를 뽑는다. 그래서 ServerHello 다음부터 암호화가 가능하다.
  - **"Ephemeral"이 중요한 이유 — 전방 비밀성(forward secrecy)**: TLS 1.2의 RSA 키 교환은 서버의 고정 개인키로 세션 키를 풀었다. 그래서 나중에 그 개인키가 털리면, 녹화해 둔 **과거 트래픽까지 전부** 풀렸다. DHE는 매 연결의 a, b를 쓰고 바로 버리므로, 서버 개인키가 털려도 과거 대화는 안전하다. TLS 1.3이 키 교환을 (EC)DHE만 허용하는 이유다.
  - **그럼 서버 인증서의 개인키는 뭐에 쓰나**: 키 교환이 아니라 **CertificateVerify 서명**(내가 진짜 서버라는 증명)에만 쓴다. "키 합의(DHE)"와 "신원 증명(인증서)"이 분리돼 있다.
  - **직접 해 보기**: OpenSSL로 X25519 키 쌍 두 개를 만들고, 서로의 공개키로 공유 비밀을 계산하면 같은 값이 나온다(실제로 돌려서 같은 값이 나오는 것을 확인했다).
    ```bash
    openssl genpkey -algorithm X25519 -out alice.pem && openssl pkey -in alice.pem -pubout -out alice.pub
    openssl genpkey -algorithm X25519 -out bob.pem   && openssl pkey -in bob.pem   -pubout -out bob.pub
    openssl pkeyutl -derive -inkey alice.pem -peerkey bob.pub   | xxd -p -c64
    openssl pkeyutl -derive -inkey bob.pem   -peerkey alice.pub | xxd -p -c64   # 위와 같은 값!
    ```
- 더 보기: README [어떻게 동작하나](README.md#어떻게-동작하나--tls-13-핸드셰이크-1-rtt) 2번(ServerHello)과 "TLS 1.2와의 차이"

### Q. SAN이 뭐야?
- 날짜: 2026-11-10
- 답: **SAN = Subject Alternative Name.** 인증서 안에 들어 있는 "**이 인증서를 쓸 수 있는 이름 목록**"이다. X.509 인증서의 확장 필드이고, 도메인 이름(DNS)이나 IP 주소를 여러 개 넣을 수 있다.
  - **실제 example.com 인증서의 SAN**:
    ```
    $ openssl x509 -in ex.pem -noout -ext subjectAltName
    X509v3 Subject Alternative Name:
        DNS:example.com, DNS:*.example.com
    ```
    인증서 하나로 `example.com`과 그 서브도메인을 모두 커버한다.
  - **클라이언트가 하는 일**: 접속한 주소(= SNI로 보낸 이름)가 SAN 목록에 **있는지** 확인하고, 없으면 연결을 끊는다. 서명 체인이 완벽해도 이름이 다르면 실패한다. 남의 사이트용으로 정당하게 발급된 인증서를 가로채서 다른 도메인에 쓰는 것을 막는 장치다.
  - **CN과의 관계**: 예전에는 인증서의 주체 CN(Common Name)에 도메인을 하나 적었다. 지금은 브라우저와 대부분의 TLS 라이브러리가 호스트 이름을 검증할 때 **SAN만 본다**. CN은 사람이 읽는 표시용에 가깝다.
  - **와일드카드 규칙**: `*.example.com`은 **한 단계**만 대신한다 (`openssl x509 -checkhost`로 확인):
    ```
    example.com      → match      (SAN에 따로 적혀 있어서)
    www.example.com  → match      (*.example.com)
    a.b.example.com  → NOT match  (* 는 점을 넘지 못함)
    ```
  - **이름이 안 맞을 때의 실제 오류**: 실습 4번의 `localhost` 인증서(SAN=`DNS:localhost`)로 띄운 서버에 IP로 접속하면:
    ```
    $ curl --cacert cert.pem https://127.0.0.1:8443/
    curl: (60) SSL: no alternative certificate subject name matches target ipv4 address '127.0.0.1'
    ```
    인증서는 신뢰하도록 지정했지만, SAN에 `127.0.0.1`이 없어서 실패한다. `-addext "subjectAltName=DNS:localhost,IP:127.0.0.1"`로 다시 만들면 통과한다.
  - **연결 고리**: SNI(어느 이름으로 접속하는지 알림) → 서버가 그 이름의 인증서 선택 → 클라이언트가 SAN으로 이름 확인. `lab/tls_client.py`의 `server_hostname=host`가 SNI와 SAN 검증에 함께 쓰이는 이유다.
- 더 보기: README [인증서는 왜 믿을 수 있나](README.md#인증서는-왜-믿을-수-있나--신뢰-체인) ③번, 위의 "SNI는 뭐야?"

### Q. `echo | openssl s_client -connect example.com:443 -servername example.com -brief` 를 하나씩 뜯어서 설명해줘
- 날짜: 2026-11-10
- 답: 조각별로 보면 이렇다. 아래 내용은 모두 `man openssl-s_client` 확인과 직접 실행으로 검증했다.

  | 조각 | 뜻 |
  |---|---|
  | `echo` | 빈 줄 하나를 출력하고 끝난다. 끝나면서 **EOF(입력 끝)** 신호가 간다. |
  | `\|` | 파이프. 왼쪽의 출력을 오른쪽 명령의 **표준입력(stdin)**으로 넘긴다. |
  | `openssl` | 암호 도구 모음. 뒤에 하위 명령을 붙여 쓴다 (`x509`, `genpkey`, `s_server` 등). |
  | `s_client` | **TLS 클라이언트**. 서버에 TCP로 붙고 TLS 핸드셰이크까지 해 준다. 브라우저에서 화면만 뺀 것이라고 생각하면 된다. |
  | `-connect example.com:443` | 접속할 `호스트:포트`. DNS로 IP를 찾아 TCP 연결을 연다. 443은 HTTPS 기본 포트다. |
  | `-servername example.com` | ClientHello의 **SNI** 값. 사실 OpenSSL 1.1.1부터는 생략해도 `-connect`의 도메인이 자동으로 들어간다. 그래서 IP로 접속하거나 다른 이름을 보내고 싶을 때 주로 쓴다. 이번 명령에서는 "명시적으로 보여주기" 용도다. |
  | `-brief` | 인증서 원문, 세션 정보 같은 긴 출력 대신 **요약 몇 줄**만 보여준다. |

  **왜 `echo |`를 붙이나?** `s_client`는 연결이 되면 키보드 입력을 기다린다. 입력한 내용을 암호화해서 서버로 보내는 대화 모드이기 때문이다. `echo |`를 붙이면 빈 줄을 보내고 곧바로 EOF가 오고, s_client는 입력이 끝났으니 연결을 닫고 종료한다. 그래서 **"핸드셰이크만 하고 바로 끝내기"**가 된다. 빼면 커서가 멈춘 채 기다리고, `Ctrl+C`로 빠져나와야 한다.

  **출력 한 줄씩 읽기** (example.com 실제 결과):
  ```
  Connecting to 104.20.23.154           ← DNS로 찾은 IP에 TCP 연결 시도
  CONNECTION ESTABLISHED                ← TCP + TLS 핸드셰이크 성공
  Protocol version: TLSv1.3             ← 합의한 TLS 버전
  Ciphersuite: TLS_AES_256_GCM_SHA384   ← 레코드 암호화는 AES-256-GCM(AEAD), 키 파생은 SHA-384
  Peer certificate: CN=example.com      ← 서버 인증서의 주체
  Hash used: SHA256                     ┐ CertificateVerify 서명에 쓴 알고리즘:
  Signature type: ecdsa_secp256r1_sha256┘ 서버가 ECDSA(P-256) 키로 서명했다
  Verification: OK                      ← 인증서 체인을 신뢰 루트까지 검증 성공
  Negotiated TLS1.3 group: X25519MLKEM768 ← 키 교환(ECDHE) 그룹. X25519 + 양자내성 ML-KEM 하이브리드
  DONE                                  ← EOF를 받아 연결 종료
  ```

  **알아두면 좋은 함정 3가지 (직접 확인함)**
  1. **`-brief` 요약은 stderr로 나온다.** 그래서 `| grep`으로 거르려면 `2>&1`을 붙여야 한다. 예: `echo | openssl s_client -connect example.com:443 -brief 2>&1 | grep Protocol`
  2. **검증에 실패해도 연결은 계속된다.** 자체 서명 서버에 붙으면 `Verification error: self-signed certificate`가 찍히지만 `CONNECTION ESTABLISHED`이고 종료 코드도 0이다. s_client는 진단 도구라서 일부러 그렇게 동작한다. 실패 시 끊게 하려면 `-verify_return_error`를 붙인다.
  3. **`Verification: OK`는 호스트 이름(SAN)까지 확인한 결과가 아니다.** `-servername evil.com`으로 localhost 인증서 서버에 붙어도 `Verification: OK`가 나왔다. 이름까지 보려면 `-verify_hostname example.com`을 붙여야 하고, 그러면 `Verification error: hostname mismatch`가 나온다. 브라우저, curl, Python `ssl.create_default_context()`는 이름 검증을 기본으로 한다.
- 더 보기: `man openssl-s_client`, 위의 "SNI는 뭐야?", "SAN이 뭐야?", "AEAD 암호가 뭐야?", "DHE는 뭐야?"

### Q. `-msg` 결과를 보면 클라이언트는 서버에게 Finished를 안 보낸 것 같은데 왜 그래?
- 날짜: 2026-11-10
- 답: 보냈다. `>>>`(클라이언트가 보냄) 쪽에 `>>> TLS 1.3, Handshake [length 0034], Finished`가 있다. 그 사이에 끼어 있는 `RecordHeader`, `ChangeCipherSpec`, `InnerContent` 줄 때문에 잘 안 보였을 뿐이다. 길이 `0x34`(52바이트)는 메시지 헤더 4바이트와 SHA-384 해시 48바이트를 더한 값이다. 서버 Finished도 길이가 같다.
  - `ChangeCipherSpec`: TLS 1.3에서는 의미가 없다. 1.2처럼 보이게 해서 오래된 중간 장비(미들박스)를 통과하려고 보내는 호환용 메시지다.
  - `InnerContent [length 0001]`: 암호화된 레코드 안에 숨긴 실제 종류(content type) 1바이트다.
  - Finished 뒤에 나오는 레코드: `echo`가 보낸 줄바꿈(Application Data)과 `close_notify` 알림이다. `</dev/null`로 입력을 주면 Application Data 레코드가 없어지는 것을 확인했다.

### Q. 자체 서명 실습의 `openssl req ...`, `openssl s_server ...` 각 옵션이 무슨 역할이야? s_server는 서버를 여는 거야?
- 날짜: 2026-11-10
- 답: `openssl req`는 원래 인증서 서명 요청(CSR)을 만드는 명령이다. `-x509`를 붙이면 CSR 대신 **자기가 서명한 인증서**를 바로 만들고, `-newkey`가 있으면 개인키도 같이 만든다. `s_server`는 맞다. 지정한 포트에서 TLS 서버를 연다(테스트용).

  | 옵션 | 역할 |
  |---|---|
  | `-x509` | CSR 대신 자체 서명 인증서를 출력 |
  | `-newkey ec` | 새 타원곡선(EC) 개인키 생성 |
  | `-pkeyopt ec_paramgen_curve:P-256` | 곡선을 P-256으로 지정 |
  | `-nodes` | 개인키를 암호(passphrase)로 잠그지 않음 (no DES. 3.0부터는 `-noenc`가 새 이름) |
  | `-keyout key.pem` | 개인키 저장 파일 |
  | `-out cert.pem` | 인증서 저장 파일 |
  | `-days 7` | 유효기간 7일 |
  | `-subj "/CN=localhost"` | 주체(Subject) 이름. 대화형 질문 없이 바로 지정 |
  | `-addext "subjectAltName=DNS:localhost"` | SAN 확장 추가. 클라이언트가 실제로 비교하는 이름 |
  | `s_server -accept 8443` | 8443 포트에서 접속을 기다림 (기본값 4433) |
  | `-cert cert.pem -key key.pem` | 서버가 보낼 인증서와, CertificateVerify 서명에 쓸 개인키 |
  | `-www` | 접속하면 협상 정보를 HTML로 응답 (웹 서버처럼 동작) |
  | `-tls1_3` | TLS 1.3만 허용 |

  직접 실행해서 확인한 결과:
  ```
  subject=CN=localhost
  issuer=CN=localhost              ← 주체와 발급자가 같다 = 자체 서명
  notBefore=Nov 10 ... notAfter=Nov 17 ...   ← -days 7
  X509v3 Subject Alternative Name: DNS:localhost
  Private-Key: (256 bit) / NIST CURVE: P-256

  curl https://localhost:9443/                → curl: (60) ... self-signed certificate (18)
  curl --cacert cert.pem https://localhost:9443/  → -www 응답 HTML(TLSv1.3 암호군 목록 등)
  ```
  `--cacert cert.pem`은 "이 인증서를 신뢰 루트로 쳐라"라는 뜻이다. 자체 서명 인증서는 자기 자신이 루트라서, 이것을 신뢰 목록에 넣으면 체인 검증이 통과한다.
- 더 보기: `man openssl-req`, `man openssl-s_server`, 위의 "SAN이 뭐야?", README의 "인증서는 왜 믿을 수 있나 — 신뢰 체인"
