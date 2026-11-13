---
description: "Unity il2cpp global-metadata.dat의 -GMD 토큰 난독화 복원."
icon: table
---

# il2cpp 메타데이터 난독화

Unity IL2CPP Windows 빌드에서 CrackProof의 선택적 `-GMD` 모드는 보호 대상 PE(`GameAssembly.dll`)와 함께 `global-metadata.dat` 파일을 수정하여 모든 `Il2CppMethodDefinition` 항목의 `token` 필드를 다시 작성합니다.

## 동작 원리와 크래시 증상

IL2CPP는 시작 시점에 `(token & 0x00FFFFFF) - 1`을 인덱스로 사용해 `Il2CppCodeGenModule.methodPointers` 및 `invokerIndices` 배열에서 각 메서드의 컴파일된 코드 포인터와 인보커를 조회합니다. 두 배열의 크기는 해당 모듈의 컴파일된 메서드 수에 맞춰 할당되므로, IL2CPP가 정상 동작하려면 모듈별 `MethodDef` RID가 `1..=methodPointerCount` 범위의 연속된 수열을 이루어야 합니다.

`-GMD`는 이 연속된 RID를 희소(불연속) ECMA-335 스타일 토큰으로 치환합니다(예: 컴파일된 메서드가 약 `14,000`개인 모듈 내부에서 RID가 약 `55,000`까지 증가). 보호된 프로세스 내부에서는 IL2CPP가 메타데이터를 읽기 전에 CrackProof 런타임이 토큰을 다시 매핑하지만, `global-metadata.dat` 파일을 복원하지 않고 `GameAssembly.dll`만 정적으로 언패킹하면 `il2cpp_init` 도중 `(token_row - 1)` 인덱스가 배열 범위를 벗어나게 됩니다(주로 `System.Array` 인터페이스 메서드를 초기화할 때 `0xC0000005` 예외로 크래시 발생).

## 키가 필요 없는 구조적 복원

`Il2CppMethodDefinition` 항목은 선언 타입(`Il2CppTypeDefinition`)별로 연속 배치되고 타입 역시 모듈(`Il2CppImageDefinition`)별로 연속 배치되므로, 별도의 암호 키 없이 테이블 순서만으로 각 메서드의 정규 토큰을 바로 계산할 수 있습니다.

```text
local_index = method_index - image_first_method_index
new_token   = 0x06000000 | ((local_index + 1) & 0x00FFFFFF)
```

필드 토큰과 타입 토큰은 원래 정규 형태를 유지하므로 수정하지 않습니다. 난독화되지 않은 원본 `global-metadata.dat` 파일에 이 수식을 적용해도 `new_token`이 기존 `token`과 정확히 일치하는 멱등(idempotent) 연산입니다.

## 버전 31 레이아웃 상수

| 항목 | 값 |
| --- | --- |
| 매직 값 (`+0x00`) | `0xFAB11BAF` |
| 메타데이터 버전 (`+0x04`) | `31` |
| 헤더 `{offset, size}` 쌍 | `methods @0x30`, `types @0xA0`, `images @0xA8` |
| 레코드 스트라이드 | `method = 0x24`, `type = 0x58`, `image = 0x28` |
| 핵심 필드 | `method.token` (`+0x18`의 `u32`); `type.methodStart` (`+0x24`의 `u32`), `type.method_count` (`+0x40`의 `u16`); `image.typeStart` (`+0x08`의 `u32`), `image.typeCount` (`+0x0C`의 `u32`) |

복원된 바이트를 기록하기 전에는 항상 `0xFAB11BAF` 매직, `version == 31`, 파일 내 테이블 경계, 테이블 크기가 레코드 스트라이드로 나누어떨어지는지 여부, 각 이미지에 속한 메서드 인덱스 범위의 연속성을 검증해야 합니다. Android IL2CPP 빌드는 시드 기반 5라운드 RID 또는 `methodIndex` 순열을 사용하며 모듈 `0x0C`에서 복원됩니다(버전 31에서는 `-GMD` 방식도 폴백으로 지원하며, 자세한 내용은 [메서드 토큰](https://app.gitbook.com/s/lHw4BUMHINzsXego7Ota/metadata/method-tokens) 참고).
