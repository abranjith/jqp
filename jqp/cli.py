import json
import click
from tokenizer import get_grouped_tokens, TokenName

NULL = "null"

#from click documentation to support alias command
class AliasedGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))

@click.command()
@click.option("--expression", "-e", type=click.STRING, help="jq style expression to search in the json", required=True)
@click.option("--file", "-f", type=click.File("r"), help="File with valid json content", required=True)
def cli(expression, file):
    all_tokens = [g for g in get_grouped_tokens(expression)]
    validate_tokens(all_tokens, expression)
    json_obj = get_json(file)
    result = jq_parser(json_obj, all_tokens)
    result = json.dumps(result, indent=4)
    click.echo(result)

def jq_parser(json_obj, tokens):
    if not (json_obj and json_obj != NULL and tokens):
        return json_obj
    
    if(len(tokens) == 1):
        token = tokens[0]
        return retrieve_token_from_json(json_obj, token)
    
    first_token = tokens[0]
    remaining_tokens = tokens[1:]

    if isinstance(json_obj, list):
        result = []
        for obj in json_obj:
            r = retrieve_token_from_json(obj, first_token)
            if r and r != NULL:
                result.append(jq_parser(r, remaining_tokens))
            else:
                result.append(NULL)
        index = _get_index(first_token)
        if index is None:
            return result
        if index >= len(result):
            raise click.ClickException(f"Bad index {index}. There are only {len(result)} elements in the array")
        return result[index]
    elif isinstance(json_obj, dict):
        r = retrieve_token_from_json(json_obj, first_token)
        return jq_parser(r, remaining_tokens)

def retrieve_token_from_json(json_obj, token):
    if not (json_obj and json_obj != NULL and token):
        return json_obj
    index = _get_index(token)
    if isinstance(json_obj, list):
        result = []
        for obj in json_obj:
            #this is probably the only case for a valid json
            if isinstance(obj, dict):
                #case insensitive
                obj = {k.strip().lower() : v for k,v in obj.items()}
                result.append(obj.get(token[0].value.strip().lower(), NULL))
        if index is None:
            return result
        if index >= len(result):
            raise click.ClickException(f"Bad index {index}. There are only {len(result)} elements in the array")
        return result[index]
    elif isinstance(json_obj, dict):
        #case insensitive
        json_obj = {k.strip().lower() : v for k,v in json_obj.items()}
        val = json_obj.get(token[0].value.strip().lower(), NULL)
        if isinstance(val, list):
            if index is None:
                return val
            if index >= len(val):
                raise click.ClickException(f"Bad index {index}. There are only {len(val)} elements in the array")
            return val[index]
        return val

def get_json(fp):
    try:
        return json.load(fp)
    except Exception as ex:
        raise click.ClickException(str(ex))

def validate_tokens(all_tokens, expression):
    if not all_tokens or len(all_tokens) == 0:
        raise click.ClickException(f"{expression} is a bad expression")
    for g in all_tokens:
        if not g:
            raise click.ClickException(f"{expression} is a bad expression. Currently not supporting unix style multiple dots (such as .. etc)")
        if len(g) == 1:
            if not ( g[0].name == TokenName.KEY ):
                message = str(g[0])
                raise click.ClickException(f"{message} is a bad token. Currently supports either plain key or key with one index (in case of array)")
        elif len(g) == 2:
            if not ( g[0].name == TokenName.KEY and g[1].name == TokenName.INDEX):
                message = str(g[0]) + ", " + str(g[1])
                raise click.ClickException(f"{message} is a bad token. Currently supports either plain key or key with one index (in case of array)")
        elif len(g) > 2:
            message = ", ".join([str(r) for r in g])
            raise click.ClickException(f"{message} is a bad token. Currently supports either plain key or key with one index (in case of array)")

def _get_index(token):
    if not token or len(token) <= 1:
        return None
    t = token[1]
    if t.name == TokenName.INDEX:
        if t.value.strip().isdecimal():
            return int(t.value.strip())
        else:
            raise click.ClickException(f"{t.value} is a bad value where a numeric index of >= 0 is expected")
    return None