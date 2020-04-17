import re
from enum import Enum, unique
from collections import namedtuple

#All valid tokens
DOT = r"(?P<DOT>\.)"                                                   #matches .    
INDEX = r"(?P<INDEX>(?<=\[)(.*?)(?=\]))"                               #matches 0 in [0]               
START_TEXT = r"(?P<START_KEY>(?<!\.)([^\.\[\]]+?)((?=\.)|(?=\[)))"     #matches name in name. or name[0].
MID_TEXT = r"(?P<MID_KEY>(?<=\.)([^\.\[\]]+?)((?=\.)|(?=\[)))"         #matches name in .name. or .name[0].
END_TEXT = r"(?P<END_KEY>(?<=\.)([^\.\[\]]+?)((?!.)|(?=\[)))"          #matches name in .name or .name[0]
JUST_TEXT = r"(?P<JUST_KEY>(?<!\.)([^\.\[\]]+?)((?!.)|(?=\[)))"        #matches name in name or name[0]

@unique
class TokenName(Enum):
    NONE = 0
    DOT = 1
    INDEX= 2
    KEY = 3

    @staticmethod
    def get_token_name(name):
        if not name:
            return TokenName.NONE
        name = name.strip().upper()
        #special handling gor key
        if name.endswith("_KEY"):
            return TokenName.KEY
        value = TokenName.__members__.get(name)
        if value:
            return TokenName(value)
        return TokenName.NONE

    #string compare with name
    def __eq__(self, other):
        if isinstance(other, str):
            if str(self.name).upper() == other.strip().upper():
                return True
            return False
        return super().__eq__(other)

#returns all tokens parsed using a valid json expression
def get_jq_tokens(jq_expression):
    jq_token = namedtuple("JqToken", ["name", "value", "start_pos", "end_pos"])
    jq_token.__str__ = lambda s: f"{s.name.name} = {s.value}"
    master = re.compile("|".join([DOT, INDEX, START_TEXT, MID_TEXT, END_TEXT, JUST_TEXT]))
    scanner = master.scanner(jq_expression)
    for token in iter(scanner.search, None):
        name = TokenName.get_token_name(token.lastgroup)
        yield jq_token(name, token.group(), token.start(), token.end())

# the expression such that each group represents what can be parsed from a json in one iteration (eg: name[0])
# TODO - in case there is multi dot support (unix style), also support grouping them together. Right now it basically splits by dot
def get_grouped_tokens(jq_expression):
    #get all tokens
    all_tokens = [t for t in get_jq_tokens(jq_expression)]
    group = []
    for i, t in enumerate(all_tokens):
        if i == 0 and t.name == TokenName.DOT:
            continue
        if t.name == TokenName.DOT:
            yield group
            group = []
        else:
            group.append(t)
    yield group

if __name__ == "__main__":
    e = ".e1.e2[0][-1].e21.e3[1]"
    for t in get_jq_tokens(e):
       print(t, type(t.value))
