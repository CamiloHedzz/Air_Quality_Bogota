import React, { useEffect } from "react";
//import { Dash, dash_table } from "dash";
import {Table} from "../components/simple_table"
import ContactForm from '../components/form';



export function About() {
    
    useEffect(() => {
        const setLeftContentTop = () => {
            const navHeight = document.querySelector('.nav').offsetHeight;
            document.getElementById('leftContent').style.top = navHeight + 'px';
        };

        setLeftContentTop(); 

        window.addEventListener('resize', setLeftContentTop);

        return () => {
            window.removeEventListener('resize', setLeftContentTop); 
        };
    }, []); 

    return (
        <div id="about">
            <div id="leftContent">
                <div class="about_subtitle">
                    <h1 >Autores</h1>
                </div>
                <div id="authors">
                    <div class="author1">
                        <img src="../src/assets/images/jap.png" alt="developer" />
                        <div class ="right_auth_content">
                            <div class="auth_name">
                            <a href="https://github.com/Juanariasp">Juan Esteban Arias</a></div>
                            <div class="description_auth">
                            Juan Esteban Arias, profesional con formación en Ingeniería en Ciencias de la Computación
                            e Inteligencia Artificial. Mi participación destacada en competiciones
                            de programación a nivel nacional y regional subraya mi habilidad para abordar desafíos complejos. 
                             </div>
                        </div>
                    </div>

                    <div class="author1">
                        <img src="../src/assets/images/chi.jpg" alt="developer" />
                        <div class ="right_auth_content">
                            <div class="auth_name">
                            <a href="https://github.com/CamiloHedzz">Camilo Hernandez</a></div>
                            <div class="description_auth">
                                Ingeniero en Ciencias de la Computación e Inteligencia Artificial, 
                                interasado en siempre aprender nuevas tecnologias y practicas 
                                para procesamiento de datos y creación de modelos de Machine Learning.
                            </div>
                        </div>
                    </div>
                </div>
                <div class="about_subtitle">
                    <h1>El motivo</h1>
                </div>
                <div class="description_motive">
                La contaminación ambiental puede tener un impacto significativo en la salud de 
                las personas que viven en áreas afectadas. Una aplicación web que identifique 
                las zonas más contaminadas de Bogotá puede ayudar a los residentes a tomar medidas 
                para proteger su salud, al mostrar de manera clara y accesible los niveles de contaminación
                en diferentes áreas, se puede educar a la población sobre la importancia de tomar medidas 
                para reducir la contaminación.
                </div>
            </div>
            <div id="rightContent">
                <div class="about_subtitle">
                    <h1>¿Como recopilamos los datos?</h1>
                </div>
                <p>
                    Mediante un sistema de rutas ya definido, se circulan las 
                    calles de Bogotá con sensores PM2.5 con el fin de determinar
                    la calidad del aire. Posteriormente, esta información se 
                    somete a un procesamiento de datos utilizando herramientas 
                    y métodos como el análisis estadístico y algoritmos de 
                    Machine Learning, con el objetivo de obtener mejores 
                    predicciones sobre las zonas con mayores impactos 
                    ambientales. 
                    <Table/>
                    <br></br>
                    Estos datos procesados no solo permiten 
                    identificar áreas con problemas de calidad del aire, sino
                    que también pueden ser utilizados para implementar medidas
                    de mitigación más efectivas y políticas públicas orientadas
                    a mejorar la salud pública y reducir los efectos negativos
                    en el medio ambiente.
                    <br></br>
                    Recuerda que puedes encontrar mas informacion sobre este proyecto
                    a través de nuestro <a href="https://github.com/CamiloHedzz/Air_Quality_Bogota">repositorio en GitHub!</a>
                </p>
                <div class="about_subtitle">
                    <h1>Mas informacion</h1>
                </div>
                <p>
                    ¿Quieres explorar más sobre cómo nuestros servicios pueden 
                    beneficiarte? ¿Estás buscando oportunidades de colaboración 
                    o deseas brindar soporte a nuestra causa? ¡Nos encantaría saber
                    de ti! Estamos comprometidos a responder con prontitud a tus
                    consultas e intereses, así que no dudes en ponerte en contacto
                    con nosotros. Tu participación es fundamental para impulsar
                    nuestro crecimiento y éxito compartido.
                </p>
                <ContactForm/>
            </div>
        </div>
    );
}