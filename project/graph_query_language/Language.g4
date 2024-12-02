grammar Language;

prog: stmt *;

stmt: bind | add | remove | declare;

declare: 'let' VAR 'is' 'graph';

bind: 'let' VAR '=' expr;

remove: 'remove' ('vertex' | 'edge' | 'vertices') expr 'from' VAR;

add: 'add' ('vertex' | 'edge') expr 'to' VAR;

expr: NUM | CHAR | VAR | edgeExpr | setExpr | regexp | select;

setExpr: '[' expr (',' expr)* ']';

edgeExpr: '(' expr ',' expr ',' expr ')';

regexp
    : CHAR
    | VAR
    | '(' regexp ')'
    | regexp '|' regexp
    | regexp '^' range1
    | regexp '.' regexp
    | regexp '&' regexp
    ;

range1: '[' NUM '..' NUM? ']';

select: vFilter? vFilter? 'return' VAR(',' VAR) ? 'where' VAR 'reachable' 'from' VAR 'in' VAR 'by' expr;

vFilter: 'for' VAR 'in' expr;

SEMI: ';';
LET: 'let';
IS: 'is';
GRAPH: 'graph';
REMOVE: 'remove';
EQ: '=';
VERTEX: 'vertex';
EDGE: 'edge';
VERTICES: 'vertices';
FROM: 'from';
ADD: 'add';
TO: 'to';
SQRLEFT: '[';
SQRRIGHT: ']';
COMMA: ',';
PARLEFT: '(';
PARRIGHT: ')';
OR: '|';
POW: '^';
DOT: '.';
AND: '&';
FOR: 'for';
IN: 'in';
TWODOTS: '..';
RETURN: 'return';
WHERE: 'where';
REACHABLE: 'reachable';
BY: 'by';
VAR: [a-z][a-z_0-9] * ;
NUM: '0' | ([1-9][0-9] *);
CHAR: '"'[a-z] '"';

WS: [ \t\n\r\f]+ -> skip;
