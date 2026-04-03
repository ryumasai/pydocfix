# pydocfixのルール一覧

## Docstring

| code       | default | auto-fix | description | option |
|------------|:-------:|:--------:|-------------|--------|
| DOC001 | true    | unsafe   | セクションの順番が規定の順序と一致しない | |

## Summary

| code       | default | auto-fix | description | option |
|------------|:-------:|:--------:|-------------|--------|
| SUM001 | true    |          | サマリーがない | |
| SUM002 | true    | safe     | サマリーがピリオドで終わっていない | `period = "."` |

## Parameters

| code       | default | auto-fix | description | option |
|------------|:-------:|:--------:|-------------|--------|
| PRM001 | true    | unsafe   | シグネチャに引数があるのに`Args`/`Parameters`セクションがない | |
| PRM002 | true    | safe     | シグネチャに引数がないのに`Args`/`Parameters`セクションがある | |
| PRM003 | true    | safe     | docstringに`self`/`cls`が記載されている | |
| PRM004 | true    | unsafe   | シグネチャにある引数がdocstringにない | |
| PRM005 | true    | unsafe   | シグネチャにない引数がdocstringにある | |
| PRM006 | true    | unsafe   | docstringの引数の順序がシグネチャの引数の順序と一致しない | |
| PRM007 | true    | unsafe   | docstringに同じ引数名が重複している | |
| PRM008 | true    |          | docstringの引数に説明がない | |
| PRM009 | true    | safe     | `*args`/`**kwargs`の`*`/`**`プレフィクスがない | |
| PRM101 | true    | unsafe   | docstringの型がシグネチャの型アノテーションと一致しない | |
| PRM102 | true    | unsafe   | docstringにもシグネチャにも型がない | |
| PRM103 |         | safe     | シグネチャに型アノテーションがあるのにdocstringにも型を書いている | `type_annotation_style = "signature"` |
| PRM104 |         | unsafe   | docstringに型がない | `type_annotation_style = "docstring"` |
| PRM201 | true    | unsafe   | デフォルト値があるのにdocstringに`optional`の記載がない | |
| PRM202 |         | unsafe   | デフォルト値があるのにdocstringに`default`の記載がない | |

## Returns

| code       | default | auto-fix | description | option |
|------------|:-------:|:--------:|-------------|--------|
| RTN001 | true    | unsafe   | シグネチャに戻り値があるのに `Returns` セクションがない | |
| RTN002 | true    | safe     | シグネチャに戻り値がないのに `Returns` セクションがある | |
| RTN003 | true    |          | `Returns`のエントリに説明がない | |
| RTN101 | true    | unsafe   | docstring の型がシグネチャの戻り値アノテーションと一致しない | |
| RTN102 | true    | unsafe   | docstring にもシグネチャにも型がない | |
| RTN103 |         | safe     | シグネチャに型アノテーションがあるのに docstring にも型を書いている | `type_annotation_style = "signature"` |
| RTN104 |         | unsafe   | docstring に型がない | `type_annotation_style = "docstring"` |

## Yields

| code       | default | auto-fix | description | option |
|------------|:-------:|:--------:|-------------|--------|
| YLD001 | true    | unsafe   | ジェネレータ関数なのに `Yields` セクションがない | |
| YLD002 | true    | safe     | ジェネレータ関数でないのに `Yields` セクションがある | |
| YLD003 | true    |          | `Yields`のエントリに説明がない | |
| YLD101 | true    | unsafe   | docstring の型がシグネチャの `yield` 型と一致しない | |
| YLD102 | true    | unsafe   | docstring にもシグネチャにも型がない | |
| YLD103 |         | safe     | シグネチャに型アノテーションがあるのに docstring にも型を書いている | `type_annotation_style = "signature"` |
| YLD104 |         | unsafe   | docstring に型がない | `type_annotation_style = "docstring"` |

## Raises
| code       | default | auto-fix | description | option |
|------------|:-------:|:--------:|-------------|--------|
| RIS001 | true    | unsafe   | `raise`があるのに`Raises`セクションがない | |
| RIS002 | true    | safe     | `raise`がないのに`Raises`セクションがある | |
| RIS003 | true    |          | `Raises`のエントリに説明がない | |
| RIS004 | true    | unsafe   | `raise`されている例外がdocstringにない | |
| RIS005 | true    | unsafe   | `raise`されていない例外がdocstringにある | |


## Methods / Attributes / Formatting

🚧 将来のバージョンで追加予定
