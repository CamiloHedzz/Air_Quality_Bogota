import React, { useEffect } from "react";

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
                            <div class="description_auth">Lorem ipsum, dolor sit amet consectetur adipisicing elit. Sequi dolorem fugiat, quaerat doloribus sed voluptates ipsa aut aliquam. Deleniti culpa ipsam perspiciatis aperiam natus, excepturi voluptas inventore repudiandae sint neque?</div>
                        </div>
                    </div>

                    <div class="author1">
                        <img src="../src/assets/images/chi.jpg" alt="developer" />
                        <div class ="right_auth_content">
                            <div class="auth_name">
                            <a href="https://github.com/CamiloHedzz">Camilo Hernandez</a></div>
                            <div class="description_auth">Lorem ipsum, dolor sit amet consectetur adipisicing elit. Sequi dolorem fugiat, quaerat doloribus sed voluptates ipsa aut aliquam. Deleniti culpa ipsam perspiciatis aperiam natus, excepturi voluptas inventore repudiandae sint neque?</div>
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
                    Lorem ipsum dolor sit amet, consectetur adipisicing elit. 
                    Quo esse explicabo saepe harum quos qui necessitatibus illum 
                    atque perferendis! Earum quam ad ducimus deleniti ratione 
                    vero doloremque, est repellendus voluptates.
                    <br></br>
                    Lorem ipsum dolor sit amet, consectetur adipisicing elit. 
                    Quo esse explicabo saepe harum quos qui necessitatibus illum 
                    atque perferendis! Earum quam ad ducimus deleniti ratione 
                    vero doloremque, est repellendus voluptates.
                </p>
                <div class="about_subtitle">
                    <h1>rutas</h1>
                </div>
                <p>
                    Lorem ipsum dolor sit amet, consectetur adipisicing elit. 
                    Quo esse explicabo saepe harum quos qui necessitatibus illum 
                    atque perferendis! Earum quam ad ducimus deleniti ratione 
                    vero doloremque, est repellendus voluptates.
                    <br></br>
                    Lorem ipsum dolor sit amet, consectetur adipisicing elit. 
                    Quo esse explicabo saepe harum quos qui necessitatibus illum 
                    atque perferendis! Earum quam ad ducimus deleniti ratione 
                    vero doloremque, est repellendus voluptates.
                </p>
                <div class="about_subtitle">
                    <h1>Mas informacion</h1>
                </div>
                <p>
                    Lorem ipsum dolor sit amet, consectetur adipisicing elit. 
                    Quo esse explicabo saepe harum quos qui necessitatibus illum 
                    atque perferendis! Earum quam ad ducimus deleniti ratione 
                    vero doloremque, est repellendus voluptates.
                    <br></br>
                    Lorem ipsum dolor sit amet, consectetur adipisicing elit. 
                    Quo esse explicabo saepe harum quos qui necessitatibus illum 
                    atque perferendis! Earum quam ad ducimus deleniti ratione 
                    vero doloremque, est repellendus voluptates.
                </p>
            </div>
        </div>
    );
}