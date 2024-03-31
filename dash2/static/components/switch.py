import dash_mantine_components as dmc
from dash_iconify import DashIconify

switch =  dmc.Switch(
    offLabel=DashIconify(icon="radix-icons:moon", width=20),
    onLabel=DashIconify(icon="radix-icons:sun", width=20),
    size="xl",
    className="switch-custom",
)