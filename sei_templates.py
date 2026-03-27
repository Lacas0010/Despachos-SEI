PREFIXO_DOCUMENTO = (
    "À Subsecretaria de Bem-estar Animal (Suban),\n\n" +
    "SUJEITO A PRAZO".center(90) + "\n\n"
)

RESUMO_CRONOGRAMA = (
    "atualização do cronograma e disponibilização de novas vagas para castração, "
    "tendo em vista o relato de desatualização das informações no portal oficial"
)


def modelo_hvep(num_oficio, sei_oficio, sei_manifestacao, protocolo_ouv, assunto_resumido, prazo):
    return f"""
Trata-se do Ofício nº {num_oficio} - CACI/GAB/OUVIDORIA ({sei_oficio}) por meio do qual a Ouvidoria da Casa Civil do Distrito Federal encaminha a denúncia contida na Manifestação - Reclamação {sei_manifestacao} (SEI nº {sei_oficio}), oriundo do Sistema de Ouvidoria - OUV-DF, para conhecimento e providências cabíveis. A Reclamação da solicitante, em síntese, versa sobre {assunto_resumido}.

Encaminho os autos para conhecimento e providências, com a brevidade que o assunto requer, considerando que o prazo de resposta a esta Secretaria Executiva é, impreterivelmente, {prazo}, conforme Art. 5º, da LEI Nº 4.896, DE 31 DE JULHO DE 2012.
"""


def modelo_castracao(num_oficio, sei_oficio, sei_manifestacao, protocolo_ouv, assunto_resumido, prazo):
    return f"""
Trata-se do Ofício {num_oficio} ({sei_oficio}) encaminhado pela Ouvidoria da Casa Civil do Distrito Federal, por meio do qual se solicita análise e manifestação acerca da demanda registrada na Ouvidoria do Governo do Distrito Federal, sob o Protocolo {protocolo_ouv} ({sei_manifestacao}).

A demanda refere-se a reclamação apresentada por cidadão que relata {assunto_resumido}.

Encaminho os autos para conhecimento, análise e adoção das providências cabíveis, observando-se que o prazo para resposta a esta Secretaria Executiva é, impreterivelmente, até {prazo}, nos termos do art. 5º da Lei nº 4.896, de 31 de julho de 2012.
"""


def modelo_condicoes_hvep(num_oficio, sei_oficio, sei_manifestacao, protocolo_ouv, assunto_resumido, prazo):
    return f"""
Trata-se do Ofício nº {num_oficio} - CACI/GAB/OUVIDORIA ({sei_oficio}) por meio do qual a Ouvidoria da Casa Civil do Distrito Federal solicita providências quanto às {assunto_resumido}, conforme especifica na Manifestação ({sei_manifestacao}), referente ao Protocolo: {protocolo_ouv}.

Encaminho os autos para conhecimento e providências, com a brevidade que o assunto requer, considerando que o prazo de resposta a Secretaria Executiva é, impreterivelmente, {prazo}, conforme Art. 5º, da LEI Nº 4.896, DE 31 DE JULHO DE 2012.
"""


def modelo_cronograma_castracao(num_oficio, sei_oficio, sei_manifestacao, protocolo_ouv, assunto_resumido, prazo):
    return f"""
Trata-se do Ofício Nº {num_oficio} - CACI/GAB/OUVIDORIA ({sei_oficio}) por meio do qual a Ouvidoria da Casa Civil do Distrito Federal solicita providências quanto à atualização do cronograma e disponibilização de novas vagas para castração, tendo em vista o relato de desatualização das informações no portal oficial, conforme especifica na Manifestação ({sei_manifestacao}), referente ao Protocolo: {protocolo_ouv}.

Encaminho os autos para conhecimento e providências, com a brevidade que o assunto requer, considerando que o prazo de resposta a Secretaria Executiva é, impreterivelmente, {prazo}, conforme Art. 5º, da LEI Nº 4.896, DE 31 DE JULHO DE 2012.
"""
