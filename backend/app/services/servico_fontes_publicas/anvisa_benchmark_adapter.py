class AnvisaBenchmarkAdapter:
    """Adapter de benchmark Anvisa.

    Nesta versão não faz scraping nem leitura automática de boletins. O adapter
    formaliza o ponto onde uma futura API ou dataset oficial poderá entrar.
    """

    def suporta_importacao_automatica(self) -> bool:
        return False
