def test_ci_pipeline_is_alive():
    """
    Teste estrutural primário (Sanity Check).
    Garante que o runner do GitHub consegue localizar a pasta tests,
    coletar os arquivos e executar o pytest com sucesso (Exit Code 0).
    """
    perimetro_seguro = True
    assert perimetro_seguro is True