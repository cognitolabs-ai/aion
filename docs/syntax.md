---
doc-id: aion-syntax-v1
title: Aion Syntax (EBNF – Minimal Subset)
tags: syntax, ebnf, grammar, mts
last-updated: 2026-03-17
---

# Aion Syntax (Minimal Subset)

The full grammar is evolving. This subset is sufficient for the demo and examples.

EBNF (ISO/IEC 14977 inspired)

```
file        ::= intent_block function_def ;
intent_block::= "#intent" NL { intent_kv NL } ;
intent_kv   ::= "#" WS? ("goal"|"pre"|"post") ":" TEXT ;

function_def::= "fn" IDENT "(" arg_list ")" "->" type "{" NL
                 body_lines
                 "}" ;

arg_list    ::= { ANYCHAR - ")" } ;
type        ::= { ANYCHAR - "{" } ;

body_lines  ::= pipeline_expr NL ;
pipeline_expr::= IDENT { "|" stage } ;
stage       ::= IDENT "(" { ANYCHAR - ")" } ")"
              | IDENT "." IDENT "(" { ANYCHAR - ")" } ")"  (* module call like http.get(...) *)
              | "match" "{" { ANYCHAR - "}" } "}" ;

IDENT       ::= letter { letter | digit | "_" } ;
TEXT        ::= { any character except NL } ;
NL          ::= "\n" | "\r\n" ;
WS          ::= " " | "\t" ;
```

Struct Literals and Strings

```
struct-lit  ::= IDENT "{" field-list "}" ;
field-list  ::= IDENT ":" expr { "," IDENT ":" expr } ;
string      ::= "\"" { char | interp } "\"" | "'" { char | interp } "'" ;
interp      ::= "${" expr "}" ;
```

Notes
- Minimally Tokenized Syntax (MTS) omits human-centric spacing. The parser ignores extraneous whitespace.
- Verify blocks are specified but out of scope for this minimal grammar and demo.
