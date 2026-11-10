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
