#!/usr/bin/env python3
"""公開入口の直接呼び出しから、旧設定解決scriptへの参照へ戻る変更を拒否する。

正本: shared/consumer-contract/nested-playbook.md の直接呼び出し契約。
入力: 公開6入口配下のMarkdown・playbook.ymlと共通の呼び出し契約。
正規化: 同梱resolverのdep_referencesによるドット形・ブラケット形の解析。
合格述語: grill/write-docのrootからprepare.sh/resolve.shを組み立てる参照がない。
診断: 違反ファイル、行番号、依存名、禁止参照。
正例: 公開entry。反例: 外部rootのprepare.sh。境界例: 同梱PLUGIN_ROOTのprepare.sh。
意味評価: 入力の妥当性、対話での明示合意、執筆内容、実際の保存成功は判定しない。
"""

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location(
    "consumer_resolver", ROOT / "shared/playbook/resolve-dependency.py")
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)


def violations(text):
    result = []
    for number, line in enumerate(text.splitlines(), 1):
        for name, segments, suffix, raw in resolver.dep_references(line):
            if (name in {"grill", "write-doc"} and segments == ["root"]
                    and suffix in {"/scripts/prepare.sh", "/scripts/resolve.sh"}):
                result.append((number, name, raw))
    return result


def self_test():
    for name in ("grill", "write-doc"):
        for reference in ("${.deps." + name + ".entry}",
                          '${.deps["' + name + '"].entry}'):
            assert not violations(reference), reference
        for accessor in ("." + name, '["' + name + '"]'):
            for script in ("prepare.sh", "resolve.sh"):
                reference = "${.deps" + accessor + ".root}/scripts/" + script
                assert len(violations(reference)) == 1, reference
    assert not violations('bash "${PLUGIN_ROOT}/scripts/prepare.sh"'), "own runtime"
    assert not violations("output_to: /tmp/dialogue-result.yml"), "grill output contract"


def main():
    self_test()
    paths = [ROOT / "shared/consumer-contract/nested-playbook.md"]
    for entry in sorted((ROOT / "plugins/playbooks/bdd").iterdir()):
        if entry.is_dir():
            paths.extend(sorted(entry.rglob("*.md")))
            paths.append(entry / "playbook.yml")
    failures = 0
    for path in paths:
        for line, name, reference in violations(path.read_text()):
            print(f"FAIL: {path}:{line}: {name} は公開entryへ直接渡す: {reference}")
            failures += 1
    if failures:
        return 1
    print("Direct consumer entry: passed (8 negative mutations, own runtime and grill output retained)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
