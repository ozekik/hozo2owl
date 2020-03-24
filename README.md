# hozo2owl

Yet another Hozo ontology to OWL ontology converter.

Coded to handle [EVT_1.3.xml](https://researchmap.jp/zoeai/event-ontology-EVT) (世界史イベントオントロジー) in my master thesis. Not intended for complete conversion.

## Usage

Edit `namespace.py` to add prefixes.

```bash
python3 hozo2owl.py EVT_1.3.xml > EVT_1.3.ttl
```

## References

- [Hozo - Ontology Editor](http://www.hozo.jp/index_jp.html)
