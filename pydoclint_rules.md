

Fetched https://jsh9.github.io/pydoclint/violation_codes.html

pydoclintのルール一覧です。

---

## DOC0xx: Docstringパースの問題

| コード | 説明 |
|--------|------|
| DOC001 | Docstringにフォーマットエラーの可能性 |
| DOC002 | Pythonファイルの構文エラー |
| DOC003 | Docstringスタイルの不一致 |

## DOC1xx: 引数に関する違反

| コード | 説明 |
|--------|------|
| DOC101 | Docstringの引数がシグネチャより少ない |
| DOC102 | Docstringの引数がシグネチャより多い |
| DOC103 | Docstringとシグネチャの引数が異なる（フォーマットエラーの可能性も） |
| DOC104 | 引数は一致するが順序が異なる |
| DOC105 | 引数名は一致するが型ヒントが不一致 |
| DOC106 | `--arg-type-hints-in-signature=True` だがシグネチャに型ヒントがない |
| DOC107 | `--arg-type-hints-in-signature=True` だが一部の引数に型ヒントがない |
| DOC108 | `--arg-type-hints-in-signature=False` だがシグネチャに型ヒントがある |
| DOC109 | `--arg-type-hints-in-docstring=True` だがDocstringの引数リストに型ヒントがない |
| DOC110 | `--arg-type-hints-in-docstring=True` だが一部の引数に型ヒントがない |
| DOC111 | `--arg-type-hints-in-docstring=False` だがDocstringの引数リストに型ヒントがある |

## DOC2xx: 戻り値に関する違反

| コード | 説明 |
|--------|------|
| DOC201 | 関数にreturnがあるがDocstringにReturnsセクションがない |
| DOC202 | DocstringにReturnsセクションがあるがreturn文/アノテーションがない |
| DOC203 | DocstringのReturnsの型とreturnアノテーションが不一致 |

## DOC3xx: クラスDocstringとコンストラクタに関する違反

| コード | 説明 |
|--------|------|
| DOC301 | `__init__()` にDocstringがある（クラスのDocstringと統合すべき） |
| DOC302 | クラスDocstringにReturnsセクションは不要 |
| DOC303 | `__init__()` のDocstringにReturnsセクションは不要 |
| DOC304 | クラスDocstringに引数セクションがある（`__init__()` に書くべき） |
| DOC305 | クラスDocstringにRaisesセクションがある（`__init__()` に書くべき） |
| DOC306 | クラスDocstringにYieldsセクションは不要 |
| DOC307 | `__init__()` のDocstringにYieldsセクションは不要 |

## DOC4xx: yield文に関する違反

| コード | 説明 |
|--------|------|
| DOC401 | （非推奨・廃止） |
| DOC402 | 関数にyieldがあるがDocstringにYieldsセクションがない |
| DOC403 | DocstringにYieldsセクションがあるがyield文/Generator型アノテーションがない |
| DOC404 | DocstringのYieldsの型とreturnアノテーションが不一致 |

## DOC5xx: raise/assert文に関する違反

| コード | 説明 |
|--------|------|
| DOC501 | 関数にraise文があるがDocstringにRaisesセクションがない |
| DOC502 | DocstringにRaisesセクションがあるがraise文がない |
| DOC503 | DocstringのRaisesの例外と関数本体の例外が不一致 |
| DOC504 | 関数にassert文があるがDocstringにRaisesセクションがない（AssertErrorの可能性） |

## DOC6xx: クラス属性に関する違反

| コード | 説明 |
|--------|------|
| DOC601 | DocstringのクラスAttributesが実際より少ない |
| DOC602 | DocstringのクラスAttributesが実際より多い |
| DOC603 | Docstringと実際のクラス属性が異なる |
| DOC604 | 属性は一致するが順序が異なる |
| DOC605 | 属性名は一致するが型ヒントが不一致 |
