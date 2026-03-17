--------------------------------------------------------------------------------
//===-- AionCompiler.h - Glavni orkestrator prevajalnika Aion -------------===//
//
// Ta datoteka je del Aion prevajalniškega ekosistema in je izdana pod
// standardno odprtokodno licenco (MIT).
//
//===----------------------------------------------------------------------===//
///
/// \file
/// \brief Implementacija glavnega orkestratorja prevajalnika za jezik Aion.
///
/// Ta datoteka vsebuje definicijo razredov za branje "Minimally Tokenized" 
/// sintakse, pretvorbo v abstraktna sintaksna drevesa (AST) in nadzor nad 
/// postopno verifikacijo pred spustom kode v MLIR/LLVM zaledje.
///
//===----------------------------------------------------------------------===//

#ifndef AION_COMPILER_H
#define AION_COMPILER_H

#include <string>
#include "mlir/IR/BuiltinOps.h"
#include "aion/AST/ASTNode.h"

namespace aion {

/// \brief Razred za preverjanje logičnih namer in formalno verifikacijo kode.
///
/// Ta razred aplicira aksiomatično semantiko na AST. Preverja skladnost
/// med FQL specifikacijami iz `#intent` bloka in dejansko izvajalno logiko.
/// V primeru nezmožnosti dokazovanja sproži asinhron klic zunanjega LLM API-ja
/// za razrešitev stanja "Not Sure".
class IntentVerifier {
public:
    /// \brief Matematično preveri ustreznost generiranega AST vozlišča.
    ///
    /// Algoritem zgradi Hoareove trojice in poskuša dokazati, da izvajalna logika
    /// zadovolji predpogoje in postpogoje definirane s strani umetne inteligence.
    ///
    /// \param functionNode AST vozlišče, ki predstavlja celotno funkcijo vključno 
    /// z `#intent` in `verify` bloki.
    /// \returns \p true, če je koda stoodstotno varna in dokazljiva, oziroma 
    /// \p false, če preverjanje logike spodleti.
    bool verifyIntent(ASTNode* functionNode);
};

/// \brief Glavni vmesnik za prevajanje Aion kode.
///
/// Razred \p AionCompiler povezuje prednji del (Lexer in Parser) z
/// verifikatorjem namer in MLIR generatorjem strojne kode. 
class AionCompiler {
public:
    AionCompiler();
    ~AionCompiler();

    /// \brief Prevede Aion izvorno kodo v strojno specifičen LLVM IR.
    ///
    /// Metoda najprej zgradi abstraktno sintaksno drevo (AST) z ignoriranjem
    /// vizualnih formatirnih žetonov. Zatem invocira \p IntentVerifier. 
    /// Če je koda varna, jo postopno spusti skozi \p AionHL in \p linalg 
    /// narečja za samodejno strojno uglaševanje (autotuning).
    ///
    /// \param sourceCode Surovo besedilo, napisano v jeziku Aion.
    /// \param targetArchitecture Določa ciljno strojno opremo (npr. "x86_64" ali "nvptx64" za GPU).
    /// \returns Kazalec na generirani MLIR modul. V primeru, da
    /// verifikacija `#intent` specifikacije ne uspe ali koda vsebuje
    /// neobravnavane `null` tipe, vrne \p nullptr.
    ///
    /// \code
    ///   aion::AionCompiler compiler;
    ///   std::string code = "#intent ... fn main() -> Int32 { ... }";
    ///   mlir::ModuleOp* module = compiler.compile(code, "x86_64");
    ///   if (!module) {
    ///       // Obravnava napake v verifikaciji
    ///   }
    /// \endcode
    mlir::ModuleOp* compile(const std::string& sourceCode, const std::string& targetArchitecture);
};

} // namespace aion

#endif // AION_COMPILER_H