from dash import html
from PIL import Image

pil_image = Image.open("./dash2/static/images/logo.png")

icons = html.Div(
    className="icon-container",
    children=[
        html.A(
            href="https://www.linkedin.com/in/camilo-hern%C3%A1ndez-02080a237/",
            target="_blank",  # Abrir enlace en una nueva pestaña
            children=html.Img(src="/static/images/linkedin.png", alt="LinkedIn")
        ),
        html.A(
            href="https://www.instagram.com/cher_zi/",
            target="_blank",  # Abrir enlace en una nueva pestaña
            children=html.Img(src="/static/images/instagram.png", alt="Instagram")
        ),
        html.A(
            href="https://github.com/CamiloHedzz/Air_Quality_Bogota",
            target="_blank",  # Abrir enlace en una nueva pestaña
            children=html.Img(src="/static/images/github.png", alt="GitHub")
        ),
        html.A(
            href="https://youtube.com/",
            target="_blank",  # Abrir enlace en una nueva pestaña
            children=html.Img(src="/static/images/youtube.png", alt="YouTube")
        ),
    ]
)
footer_content = html.Footer(
    className="footer-content",
    children=[
        html.Div(
            className="contact-info",
            children=[
                html.Div(className="container_first_row",
                    children=[
                    html.Div(className="left_contact_col",
                             children=[
                                 html.Img(src="/static/images/logo.png", className="footer_image"),
                                 html.P("Nuestro estudio es acerca la contaminacion en la ciudad de Bogota y de como se puede visualizar meiante medios digitales.")]
                             ),
                    html.Div(className="right_contact_col",
                            children=[
                                 html.H1("Contacto"),
                                 html.P("Calle 71 # 14-14"),
                                 html.P("+57 3232397270"),
                                 html.P("camilohedzz@gmail.com"),
                                 html.H1("Redes Sociales"),
                                 icons
                            ]
                            )
                    ]
                ),
                html.Div(
                    className="bottom_contact_row",
                    children=[html.P("Si tienes dudas o quedaste con ganas de mas, no dudes revisar nuestras redes sociales y recuerda que te puedes poner en contacto con nostros, además revisa los recursos que te hemos dejado para mayor información!")])    
            ]
        )
    ]
)