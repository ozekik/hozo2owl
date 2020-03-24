# hozo2owl

Yet another Hozo ontology to OWL ontology converter.

Coded to handle [EVT_.1.3.xml](https://researchmap.jp/zoeai/event-ontology-EVT) (世界史イベントオントロジー) in my master thesis. Not intended for complete conversion.

## Usage

Edit `namespace.py` to add prefixes.

```bash
python3 hozo2owl.py EVT_.1.3.xml > EVT_.1.3.ttl
```