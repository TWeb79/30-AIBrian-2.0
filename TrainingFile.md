SNN_BOOTSTRAP start


PHASE signals

TOKEN start
TOKEN end
TOKEN object
TOKEN action
TOKEN property
TOKEN relation
TOKEN concept
TOKEN question
TOKEN answer


PHASE objects

OBJECT mensch
OBJECT human

OBJECT tier
OBJECT animal

OBJECT hund
OBJECT dog

OBJECT katze
OBJECT cat

OBJECT vogel
OBJECT bird

OBJECT baum
OBJECT tree

OBJECT wasser
OBJECT water

OBJECT sonne
OBJECT sun

OBJECT haus
OBJECT house

OBJECT nahrung
OBJECT food


PHASE properties

PROPERTY gross
PROPERTY klein
PROPERTY warm
PROPERTY kalt
PROPERTY schnell
PROPERTY langsam
PROPERTY lebendig
PROPERTY still


PHASE relations

mensch ist lebendig
human is alive

hund ist tier
dog is animal

katze ist tier
cat is animal

vogel kann fliegen
bird can fly

baum braucht wasser
tree needs water

sonne erzeugt licht
sun produces light

wasser unterstuetzt leben
water supports life


PHASE prediction

INPUT sonne
EXPECT licht

INPUT wasser
EXPECT leben

INPUT hund
EXPECT tier

INPUT katze
EXPECT tier

INPUT vogel
EXPECT fliegen


PHASE concepts

CONCEPT tier
members hund katze vogel

CONCEPT animal
members dog cat bird

CONCEPT pflanze
members baum

CONCEPT plant
members tree

CONCEPT mensch
members human


PHASE numbers

ZAHL 0
ZAHL 1
ZAHL 2
ZAHL 3
ZAHL 4
ZAHL 5
ZAHL 6
ZAHL 7
ZAHL 8
ZAHL 9
ZAHL 10

1 plus 1 gleich 2
2 plus 2 gleich 4
3 plus 2 gleich 5

5 minus 2 gleich 3
4 minus 1 gleich 3

2 mal 2 gleich 4
3 mal 3 gleich 9

4 geteilt_durch 2 gleich 2


PHASE logic

wenn 2 groesser_als 1 dann wahr
if 2 greater_than 1 then true

wenn 1 groesser_als 2 dann falsch
if 1 greater_than 2 then false

wahr und wahr gleich wahr
true and true equals true

wahr und falsch gleich falsch
true and false equals false


PHASE space_time

links
rechts
oben
unten
nah
fern

left
right
above
below
near
far

vorher
nachher
jetzt
spaeter

before
after
now
later


PHASE grammar_de

satz struktur subjekt verb objekt

ich sehe hund
du siehst katze
er sieht vogel


PHASE grammar_en

sentence structure subject verb object

i see dog
you see cat
he sees bird


PHASE dialogue

hallo → hallo
hello → hello

wer_bist_du → ich_bin_assistent
who_are_you → i_am_assistant

wie_geht_es_dir → mir_geht_es_gut
how_are_you → i_am_well

hilf_mir → ich_helfe_dir
help_me → i_help_you


PHASE emotion

mensch traurig → trost
human sad → comfort

mensch froh → bestaetigung
human happy → reinforcement

mensch muede → ruhe
human tired → rest


PHASE narrative

mensch hungrig
mensch isst nahrung
mensch zufrieden

human hungry
human eats food
human satisfied


PHASE metaphor

licht bedeutet hoffnung
light means hope

weg bedeutet leben
path means life

fluss bedeutet zeit
river means time


PHASE self_model

assistent lernt
assistant learns

assistent antwortet
assistant responds

assistent verbessert sich
assistant improves


PHASE social_rules

zuhoeren gut
listening good

unterbrechen schlecht
interrupting bad

helfen gut
helping good

verletzen schlecht
hurting bad


PHASE goals

ziel verstehen mensch
goal understand human

ziel antworten korrekt
goal answer correctly

ziel lernen weiter
goal continue learning


SNN_BOOTSTRAP ende


SNN_MATH_BOOTSTRAP start


PHASE number_identity

0 equals zero
1 equals one
2 equals two
3 equals three
4 equals four
5 equals five
6 equals six
7 equals seven
8 equals eight
9 equals nine
10 equals ten


PHASE number_ordering

2 greater_than 1
3 greater_than 2
4 greater_than 3
5 greater_than 4
6 greater_than 5

1 less_than 2
2 less_than 3
3 less_than 4
4 less_than 5
5 less_than 6

5 equal 5
6 equal 6
7 equal 7


PHASE counting_sequence

1 before 2
2 before 3
3 before 4
4 before 5
5 before 6
6 before 7
7 before 8
8 before 9
9 before 10


PHASE counting_prediction

INPUT 1 EXPECT 2
INPUT 2 EXPECT 3
INPUT 3 EXPECT 4
INPUT 4 EXPECT 5


PHASE addition

1 plus 1 equals 2
2 plus 1 equals 3
2 plus 2 equals 4
3 plus 2 equals 5
4 plus 1 equals 5
3 plus 3 equals 6
4 plus 2 equals 6


PHASE addition_inverse

2 equals 1 plus 1
3 equals 2 plus 1
4 equals 2 plus 2
5 equals 3 plus 2
6 equals 3 plus 3


PHASE subtraction

5 minus 1 equals 4
5 minus 2 equals 3
6 minus 3 equals 3
7 minus 2 equals 5
8 minus 4 equals 4


PHASE subtraction_inverse

4 plus 1 equals 5
3 plus 2 equals 5
3 plus 3 equals 6


PHASE multiplication_meaning

2 times 2 equals 4
2 times 3 equals 6
3 times 3 equals 9

2 plus 2 equals 4
2 plus 2 plus 2 equals 6
3 plus 3 plus 3 equals 9


PHASE multiplication_prediction

INPUT 2 times 2 EXPECT 4
INPUT 2 times 3 EXPECT 6
INPUT 3 times 3 EXPECT 9


PHASE division_meaning

6 divide 2 equals 3
8 divide 2 equals 4
9 divide 3 equals 3


PHASE division_inverse

3 times 2 equals 6
4 times 2 equals 8
3 times 3 equals 9


PHASE equation_structure

left_side equals right_side

2 plus 3 equals 5
4 plus 2 equals 6


PHASE algebra_variables

x is number
y is number
z is number


PHASE algebra_equations_level1

x plus 2 equals 5
x equals 3

x plus 4 equals 9
x equals 5

y minus 3 equals 2
y equals 5


PHASE algebra_equations_level2

x plus 3 equals 7
x equals 4

x minus 5 equals 2
x equals 7

y plus 6 equals 10
y equals 4


PHASE transformation_rules

x plus a equals b
x equals b minus a

x minus a equals b
x equals b plus a


PHASE reasoning_chain

INPUT hunger EXPECT food
INPUT food EXPECT energy
INPUT energy EXPECT movement

INPUT number EXPECT operation
INPUT operation EXPECT result


PHASE equality_concept

5 equals 5
3 plus 2 equals 5
2 plus 3 equals 5


PHASE comparison_reasoning

5 greater_than 3
3 less_than 5

7 greater_than 4
4 less_than 7


PHASE numeric_prediction_chain

INPUT 2 plus 2 EXPECT 4
INPUT 4 plus 2 EXPECT 6
INPUT 6 minus 2 EXPECT 4


PHASE goal_math_reasoning

goal detect numbers
goal detect relations
goal predict results
goal solve equations
goal reduce prediction_error


SNN_MATH_BOOTSTRAP end