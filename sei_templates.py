PREFIXO_DOCUMENTO = (
    "À Subsecretaria de Bem-estar Animal (Suban),\n\n" +
    "SUJEITO A PRAZO".center(90) + "\n\n"
)

RESUMO_CRONOGRAMA = (
    "atualização do cronograma e disponibilização de novas vagas para castração, "
    "tendo em vista o relato de desatualização das informações no portal oficial"
)

MODELO_HVEP = """
Trata-se do Ofício nº {NUM_OFICIO} - CACI/GAB/OUVIDORIA ({SEI_OFICIO}) por meio do qual a Ouvidoria da Casa Civil do Distrito Federal encaminha a denúncia contida na Manifestação - Reclamação {SEI_MANIFESTACAO} (SEI nº {SEI_OFICIO}), oriundo do Sistema de Ouvidoria - OUV-DF, para conhecimento e providências cabíveis. A Reclamação da solicitante, em síntese, versa sobre {RESUMO}.

Encaminho os autos para conhecimento e providências, com a brevidade que o assunto requer, considerando que o prazo de resposta a esta Secretaria Executiva é, impreterivelmente, {PRAZO}, conforme Art. 5º, da LEI Nº 4.896, DE 31 DE JULHO DE 2012.
"""

MODELO_CASTRACAO = """
Trata-se do Ofício {NUM_OFICIO} ({SEI_OFICIO}) encaminhado pela Ouvidoria da Casa Civil do Distrito Federal, por meio do qual se solicita análise e manifestação acerca da demanda registrada na Ouvidoria do Governo do Distrito Federal, sob o Protocolo {PROTOCOLO} ({SEI_MANIFESTACAO}).

A demanda refere-se a reclamação apresentada por cidadão que relata {RESUMO}.

Encaminho os autos para conhecimento, análise e adoção das providências cabíveis, observando-se que o prazo para resposta a esta Secretaria Executiva é, impreterivelmente, até {PRAZO}, nos termos do art. 5º da Lei nº 4.896, de 31 de julho de 2012.
"""

MODELO_CONDICOES_HVEP = """
Trata-se do Ofício nº {NUM_OFICIO} - CACI/GAB/OUVIDORIA ({SEI_OFICIO}) por meio do qual a Ouvidoria da Casa Civil do Distrito Federal solicita providências quanto às {RESUMO}, conforme especifica na Manifestação ({SEI_MANIFESTACAO}), referente ao Protocolo: {PROTOCOLO}.

Encaminho os autos para conhecimento e providências, com a brevidade que o assunto requer, considerando que o prazo de resposta a Secretaria Executiva é, impreterivelmente, {PRAZO}, conforme Art. 5º, da LEI Nº 4.896, DE 31 DE JULHO DE 2012.
"""

MODELO_CRONOGRAMA_CASTRACAO = """
Trata-se do Ofício Nº {NUM_OFICIO} - CACI/GAB/OUVIDORIA ({SEI_OFICIO}) por meio do qual a Ouvidoria da Casa Civil do Distrito Federal solicita providências quanto à atualização do cronograma e disponibilização de novas vagas para castração, tendo em vista o relato de desatualização das informações no portal oficial, conforme especifica na Manifestação ({SEI_MANIFESTACAO}), referente ao Protocolo: {PROTOCOLO}.

Encaminho os autos para conhecimento e providências, com a brevidade que o assunto requer, considerando que o prazo de resposta a Secretaria Executiva é, impreterivelmente, {PRAZO}, conforme Art. 5º, da LEI Nº 4.896, DE 31 DE JULHO DE 2012.
"""
