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
