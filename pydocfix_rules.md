# pydocfixのルール一覧

## Summary

| code       | default | auto-fix | description | option |
|------------|:-------:|:--------:|-------------|--------|
| PDX-SUM001 | ✔       |          | サマリーがない | |
| PDX-SUM002 | ✔       | safe     | サマリーがピリオドで終わっていない | `period = "."` |

## Parameters

| code       | default | auto-fix | description | option |
|------------|:-------:|:--------:|-------------|--------|
| PDX-PRM001 | ✔       | unsafe   | シグネチャに引数があるのに`Args`/`Parameters`セクションがない | |
| PDX-PRM002 | ✔       | safe     | シグネチャに引数がないのに`Args`/`Parameters`セクションがある | |
| PDX-PRM003 | ✔       | safe     | docstringに`self`/`cls`が記載されている | |
| PDX-PRM004 | ✔       | unsafe   | シグネチャにある引数がdocstringにない | |
| PDX-PRM005 | ✔       | unsafe   | シグネチャにない引数がdocstringにある | |
| PDX-PRM006 | ✔       | unsafe   | docstringの引数の順序がシグネチャの引数の順序と一致しない | |
| PDX-PRM007 | ✔       | unsafe   | docstringに同じ引数名が重複している | |
| PDX-PRM008 | ✔       |          | docstringの引数に説明がない | |
| PDX-PRM009 | ✔       | safe     | `*args`/`**kwargs`の`*`/`**`プレフィクスがない | |
| PDX-PRM101 | ✔       | unsafe   | docstringの型がシグネチャの型アノテーションと一致しない | |
| PDX-PRM102 | ✔       | unsafe   | docstringにもシグネチャにも型がない | |
| PDX-PRM103 |         | safe     | シグネチャに型アノテーションがあるのにdocstringにも型を書いている | `type_annotation_style = "signature"` |
| PDX-PRM104 |         | unsafe   | docstringに型がない | `type_annotation_style = "docstring"` |
| PDX-PRM201 | ✔       | unsafe   | デフォルト値があるのにdocstringに`optional`の記載がない | |
| PDX-PRM202 |         | unsafe   | デフォルト値があるのにdocstringに`default`の記載がない | |

## Returns

| code       | default | auto-fix | description | option |
|------------|:-------:|:--------:|-------------|--------|
| PDX-RTN001 | ✔       | unsafe   | シグネチャに戻り値があるのに `Returns` セクションがない | |
| PDX-RTN002 | ✔       | safe     | シグネチャに戻り値がないのに `Returns` セクションがある | |
| PDX-RTN003 | ✔       |          | `Returns`のエントリに説明がない | |
| PDX-RTN101 | ✔       | unsafe   | docstring の型がシグネチャの戻り値アノテーションと一致しない | |
| PDX-RTN102 | ✔       | unsafe   | docstring にもシグネチャにも型がない | |
| PDX-RTN103 |         | safe     | シグネチャに型アノテーションがあるのに docstring にも型を書いている | `type_annotation_style = "signature"` |
| PDX-RTN104 |         | unsafe   | docstring に型がない | `type_annotation_style = "docstring"` |

## Yields

| code       | default | auto-fix | description | option |
|------------|:-------:|:--------:|-------------|--------|
| PDX-YLD001 | ✔       | unsafe   | ジェネレータ関数なのに `Yields` セクションがない | |
| PDX-YLD002 | ✔       | safe     | ジェネレータ関数でないのに `Yields` セクションがある | |
| PDX-YLD003 | ✔       |          | `Yields`のエントリに説明がない | |
| PDX-YLD101 | ✔       | unsafe   | docstring の型がシグネチャの `yield` 型と一致しない | |
| PDX-YLD102 | ✔       | unsafe   | docstring にもシグネチャにも型がない | |
| PDX-YLD103 |         | safe     | シグネチャに型アノテーションがあるのに docstring にも型を書いている | `type_annotation_style = "signature"` |
| PDX-YLD104 |         | unsafe   | docstring に型がない | `type_annotation_style = "docstring"` |

## Raises
| code       | default | auto-fix | description | option |
|------------|:-------:|:--------:|-------------|--------|
| PDX-RIS001 | ✔       | unsafe   | `raise`があるのに`Raises`セクションがない | |
| PDX-RIS002 | ✔       | safe     | `raise`がないのに`Raises`セクションがある | |
| PDX-RIS003 | ✔       |          | `Raises`のエントリに説明がない | |
| PDX-RIS004 | ✔       | unsafe   | `raise`されている例外がdocstringにない | |
| PDX-RIS005 | ✔       | unsafe   | `raise`されていない例外がdocstringにある | |


## Methods / Attributes / Formatting

🚧 将来のバージョンで追加予定
