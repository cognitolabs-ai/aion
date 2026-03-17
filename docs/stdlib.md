--------------------------------------------------------------------------------
---
doc-id: aion-array-module-v1
title: Tehnična specifikacija modula `Array`
purpose: API definicije, tipizacija in operacije nad nizi/matrikami (Arrays) v Aionu.
tags: stdlib, array, collections, linalg, pipeline, map, filter
last-updated: 2026-03-17
---

# Modul `Array` v standardni knjižnici Aion

**Bottom Line Up Front (BLUF):** Struktura `Array[T]` v Aionu predstavlja strogo tipiziran, dinamično razširljiv in strnjen pomnilniški medpomnilnik (buffer). Na ravni prevajalnika se matrike in operacije nad njimi samodejno znižajo (lower) v `linalg` narečje v MLIR, kar omogoča strojno neodvisno pospeševanje (vektorizacijo) na CPU in GPU. Manipulacija s podatki se primarno izvaja preko deklarativnih cevovodov (`|`), kar odpravlja potrebo po imperativnih zankah (npr. `for`, `while`).

## 1. Definicija tipa in lastnosti

Matrike v Aionu so homogene (vsi elementi morajo biti istega tipa `T`). Zaradi Aionove stroge varnosti tipov (Predictive Strong Typing) dostop do elementov izven meja matrike ne povzroči sistemske zrušitve (`IndexError` ali `segfault`), temveč varno vrne opcijski tip (`null`), ki ga mora agent obvezno obravnavati znotraj `match` bloka ali cevovoda.

## 2. Osnovne metode (Core Methods)

- `len(self) -> Int32`: Vrne število elementov v matriki. Izvajanje v kompleksnosti O(1).
- `push(self, item: T) -> Void`: Doda nov element na konec matrike.
- `pop(self) -> T?`: Odstrani in vrne zadnji element matrike. Če je matrika prazna, vrne `null`.
- `get(self, index: Int32) -> T?`: Varno dostopa do elementa na podanem indeksu. Če indeks presega meje matrike, vrne `null`.

*(Agent Note: Pri uporabi metod `pop` in `get` mora prevajalnik nujno preveriti prisotnost `null` vrednosti. Če se tip `T?` uporabi neposredno v matematični operaciji brez preverjanja, bo kompilacija zavrnjena.)*

## 3. Deklarativni cevovodni operatorji (Pipeline Operators)

Aion nadomešča tradicionalno iteracijo s prvorazrednimi funkcijami višjega reda, ki so optimizirane za paralelno izvajanje in veriženje preko operatorja `|`. Implicitni sklic na trenutni element v cevovodu je vedno označen z operatorjem `?.`.

- `map(transform: Fn(T) -> U) -> Array[U]`: Vsak element tipa `T` preslika v tip `U`.
- `filter(predicate: Fn(T) -> Bool) -> Array[T]`: Ohrani samo elemente, za katere predikat vrne `true`.
- `fold(initial: U, accumulator: Fn(U, T) -> U) -> U`: Združi elemente matrike v eno samo vrednost na podlagi začetne vrednosti in akumulatorja.
- `sort(comparator: Fn(T, T) -> Bool)? -> Array[T]`: Uredi matriko. Če primerjalnik ni podan, se uporabi privzeto naraščajoče urejanje.

## 4. Nativna validacija in primer uporabe (Pipeline Data Processing)

Spodnji primer prikazuje varno analizo podatkov, kjer AI agent preko cevovoda iz matrike odstrani neveljavne (negativne) vnose, izvede transformacijo in vrne vsoto elementov. FQL specifikacija v `#intent` bloku zagotavlja, da implementacija matematično ustreza zahtevam.

```aion
#intent
# goal: "Odstrani vse negativne vrednosti iz matrike, pomnoži preostale z 2 in vrni njihovo vsoto."
# pre: "metrics == Array[Int32]"
# post: "return == Int32 AND result is the sum of (x*2) for all x >= 0 in metrics"
fn process_and_sum_metrics(metrics: Array[Int32]) -> Int32 {
    
    // Namesto for-zanke se uporabi čisti pretok podatkov,
    // ki se v MLIR prevede kot vektorizirana linalg operacija.
    metrics 
        | filter(?. >= 0) 
        | map(?.* 2) 
        | fold(0, acc + ?.)
}

// Nativna validacija preverja izvajalno logiko v peskovniku
verify {
    assert process_and_sum_metrics([1, -5, 3, 0]) == 8
    assert process_and_sum_metrics([-1, -2, -3]) == 0
    assert process_and_sum_metrics([1]) == 20
    assert process_and_sum_metrics([]) == 0
}
5. Varno naslavljanje (Safe Indexing Example)
Če AI agent želi eksplicitno dostopati do določenega elementa (npr. prvega v matriki), ga Aion prisili v uporabo varnostnega ujemanja vzorcev (match), saj operacija get vrne T?.
#intent
# goal: "Vrni prvi element matrike, če obstaja, sicer vrni 0."
# pre: "data == Array[Int32]"
# post: "return == Int32"
fn get_safe_first(data: Array[Int32]) -> Int32 {
    data.get(0) | match {
        null => 0,
        val  => val
    }
}

***

**Zakaj je ta dokumentacija pomembna za AI agente:**
1. **Definicija `?.` operatorja**: Modeli v novih jezikih pogosto ne vedo, kako se sklicevati na anonimne elemente (v Pythonu bi to bil `lambda x: x`). Ta dokumentacija eksplicitno uči agenta, naj za to uporablja `?.`.
2. **Preprečevanje Out-of-Bounds napak**: Z navedbo, da metodi `pop()` in `get()` vračata nullable tipe (`T?`), bo AI avtomatsko generiral `match` kodo in se s tem izognil najpogostejši napaki pri delu z nizi, tj. indeksiranju izven obsega pomnilnika.
3. **Odmik od t. i. imperativnosti**: Ker AI v Pythonu obožuje zanke (npr. `for item in data`), ga BLUF in primeri opozarjajo, da je v Aionu edini in najhitrejši način za obdelavo podatkov z uporabo operatorjev cevovoda (`| map | filter`), kar omogoča prenos k MLIR strojni optimizaciji.