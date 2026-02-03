class EmailGenerator:
    def __init__(self):
        pass

    def generate_cold_email(self, recruiter_name, company_name, job_title):
        """Generates a cold email template."""
        return f"""
Assunto: Interesse na vaga de {job_title} - {company_name}

Olá {recruiter_name},

Espero que esta mensagem o encontre bem.

Meu nome é [Seu Nome] e acompanho o trabalho da {company_name} com admiração. Vi a oportunidade para {job_title} e acredito que minha experiência em [Sua Área] pode agregar muito ao time.

Gostaria muito de conversar brevemente sobre como posso contribuir com os desafios da equipe.

Atenciosamente,
[Seu Nome]
[Seu LinkedIn]
"""

    def generate_follow_up(self, recruiter_name, days_since_apply):
        """Generates a follow-up email template."""
        return f"""
Assunto: Follow-up: Candidatura para [Vaga]

Olá {recruiter_name},

Estou escrevendo para reiterar meu grande interesse na posição, para a qual me candidatei há {days_since_apply} dias.

Continuo muito entusiasmado com a possibilidade de integrar o time. Caso precisem de qualquer informação adicional, estou à disposição.

Obrigado pela atenção,
[Seu Nome]
"""
