# jqp
jq style parsing written in python

Here is a quick example,

```python
# file1.txt
{
    "name1": "val1",
    "name2" : [
        {
            "name2a" : "val2a"
        }
    ]
}
```
```sh
>>> python .\jqp\  -e .name1 -f "file1.txt"
"val1"

>>> python .\jqp\  -e .name2[0] -f "file1.txt"
{
    "name2a": "val2a"
}

>>> python .\jqp\  -e .name2.name2a[0] -f "file1.txt"
"val2a"

```

## More features coming:

*   support for string and ability to make http calls from cmd line
*   unix style navigation to fetch sibling, parent etc
*   there is a known issue with multi-level array indexing where same index is used for all levels. This will be fixed with     support for multi-index
*   output syntax highlighting
*   portable exe

