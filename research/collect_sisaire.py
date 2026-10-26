"""Exportación pública SISAIRE/SDA, por año y contaminante, con caché.

Reproduce los filtros y el botón CSV del formulario público. No usa credenciales,
no consulta otras autoridades y no fabrica observaciones si un servicio falla.
"""
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import time
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE = 'https://sisaire.ideam.gov.co/ideam-sisaire-web/consultas.xhtml'


class PublicExport:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'AirQualityBogotaResearch/0.2 (public sequential historical exports; cached)'
        response = self.session.get(BASE, timeout=60)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        self.view = soup.find('input', attrs={'name':'javax.faces.ViewState'})['value']
        self.form = soup.find('form', id='filtroForm')
        self.ajax('filtroForm:departamentoSel', {'filtroForm:departamentoSel_input':'11'})
        self.ajax('filtroForm:autoridadSel', {'filtroForm:departamentoSel_input':'11', 'filtroForm:autoridadSel_input':'44'})
        self.stations = [tag['value'] for tag in self.form.select('input[type=checkbox]')]
        self.station_names = {tag['value']:self.form.find('label', attrs={'for':tag['id']}).get_text(' ',strip=True) for tag in self.form.select('input[type=checkbox]')}
        self.base_fields = {'filtroForm:departamentoSel_input':'11', 'filtroForm:autoridadSel_input':'44', 'filtroForm:estacionesSel':self.stations}
        self.ajax('filtroForm:estacionesSel', self.base_fields, event='toggleSelect')
        options = self.form.find('select', id='filtroForm:contaminanteSel_input')
        self.variables = {tag['value'] for tag in options.find_all('option')}

    def fields(self):
        values = {}
        for tag in self.form.find_all(['input','select']):
            name = tag.get('name')
            if not name or tag.has_attr('disabled'): continue
            if tag.name == 'select':
                options = tag.find_all('option')
                option = tag.find('option', selected=True) or (options[0] if options else None)
                values[name] = option.get('value','') if option else ''
            elif tag.get('type') not in ('checkbox','radio'): values[name] = tag.get('value','')
        values['javax.faces.ViewState'] = self.view
        return values

    def ajax(self, source, overrides, *, render='filtroForm msgs-globales', event='valueChange'):
        data = self.fields(); data.update(overrides)
        data.update({'javax.faces.partial.ajax':'true','javax.faces.source':source,
                     'javax.faces.partial.execute':source if event else '@all', 'javax.faces.partial.render':render})
        if event: data.update({'javax.faces.behavior.event':event, 'javax.faces.partial.event':'change'})
        else: data[source] = source
        response = self.session.post(BASE, data=data, headers={'Faces-Request':'partial/ajax'}, timeout=180)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        error = root.find('.//error')
        if error is not None: raise ValueError('Error del formulario SISAIRE: '+''.join(error.itertext())[:300])
        for update in root.findall('.//update'):
            identity = update.get('id','')
            if 'ViewState' in identity: self.view = update.text
            elif identity == 'filtroForm': self.form = BeautifulSoup(update.text,'html.parser')
            elif identity == 'msgs-globales':
                message = BeautifulSoup(update.text or '', 'html.parser').get_text(' ', strip=True)
                if message: raise ValueError('SISAIRE: '+message[:400])
        time.sleep(1)
        return root

    def export(self, start, end, variable):
        if variable not in self.variables: raise ValueError('Variable no ofrecida por SISAIRE.')
        query = {**self.base_fields, 'filtroForm:contaminanteSel_input':variable,
                 'filtroForm:fechaIni_input':start, 'filtroForm:fechaFin_input':end, 'filtroForm:tipoSel_input':'1'}
        root = self.ajax('filtroForm:btnConsultar', query, render='contenedorResultados msgs-globales', event=None)
        result = next((BeautifulSoup(update.text,'html.parser') for update in root.findall('.//update') if update.get('id')=='contenedorResultados'),None)
        anchor = result.find('a', title='csv') if result else None
        if anchor is None: raise ValueError('SISAIRE no ofrece CSV para esta consulta; no se declara cobertura.')
        identity = re.findall(r"'([^']+)'", anchor['onclick'])[-1]
        form = anchor.find_parent('form')
        data = {tag['name']:tag.get('value','') for tag in form.find_all('input') if tag.get('name') and tag.get('type')=='hidden'}
        data.update({'javax.faces.ViewState':self.view, identity:identity})
        response = self.session.post(urljoin(BASE,form['action']),data=data,timeout=180)
        response.raise_for_status()
        if not response.headers.get('content-type','').startswith('text/csv'): raise ValueError('La exportación no es CSV.')
        return response.content


def validate_export(raw, start, end, variable):
    data = pd.read_csv(io.BytesIO(raw), encoding='utf-8-sig', keep_default_na=False)
    if list(data) != ['Estacion','Fecha inicial','Fecha final',variable]: raise ValueError('Cambió el esquema CSV de SISAIRE.')
    if data.empty: raise ValueError('Exportación horaria vacía.')
    dates = pd.to_datetime(data['Fecha inicial'],format='%Y-%m-%d %H:%M',errors='raise')
    ends = pd.to_datetime(data['Fecha final'],format='%Y-%m-%d %H:%M',errors='raise')
    if not (dates.ge(pd.Timestamp(start))&dates.lt(pd.Timestamp(end)+pd.Timedelta(days=1))).all(): raise ValueError('Fechas ajenas al periodo solicitado.')
    aligned=ends.sub(dates).isin([pd.Timedelta(minutes=59),pd.Timedelta(hours=1)])&dates.dt.minute.eq(0)
    if aligned.sum()<len(data)*.5: raise ValueError('La mayoría de los registros no corresponde a la malla horaria.')
    excluded=int((~aligned).sum())
    data=data.loc[aligned].copy()
    exact=int(data.duplicated().sum());data=data.drop_duplicates()
    conflict=data.duplicated(['Estacion','Fecha inicial'],keep=False)
    conflicting=int(conflict.sum());data=data.loc[~conflict].copy()
    pd.to_numeric(data[variable].replace({'':'NaN'}),errors='raise')
    data.attrs['excluded_unaligned_intervals']=excluded
    data.attrs['identical_duplicates_removed']=exact
    data.attrs['conflicting_duplicate_rows_excluded']=conflicting
    return data


def collect(root, *, years=range(2015,2026), variables=('PM2.5','PM10'), network=False):
    root = Path(root); cache=root/'.local/research/sisaire';cache.mkdir(parents=True,exist_ok=True)
    client = None
    for year in years:
        for variable in variables:
            start,end=f'{year}-01-01',f'{year}-12-31'
            key=f'{year}_{variable.replace(".","")}'
            path,manifest=cache/f'{key}.csv.gz',cache/f'{key}.sources.json'
            if path.exists() and manifest.exists():
                raw=gzip.decompress(path.read_bytes()); meta=json.loads(manifest.read_text(encoding='utf-8'))
                if hashlib.sha256(raw).hexdigest()!=meta['sha256']: raise ValueError('La caché SISAIRE cambió.')
            else:
                if not network: raise FileNotFoundError(f'Falta SISAIRE {key}; ejecutar con --network.')
                if client is None: client=PublicExport()
                print(f'Consultando SISAIRE {year} {variable}…',flush=True)
                received=cache/f'{key}.received.csv.gz'
                if received.exists(): raw=gzip.decompress(received.read_bytes())
                else:
                    raw=client.export(start,end,variable)
                    received.write_bytes(gzip.compress(raw,mtime=0))
                data=validate_export(raw,start,end,variable)
                meta={'source':'IDEAM SISAIRE / SDA Bogotá','url':BASE, 'variable':variable, 'unit':'µg/m³',
                      'department':'11','authority_id':'44','authority':'SISAIRE - SDA', 'start':start,'end':end,
                      'aggregation':'hour','interval_convention':'start_inclusive; end at minute 59 or next exact hour; local Bogota',
                      'station_ids':client.station_names,'sha256':hashlib.sha256(raw).hexdigest(),
                      'rows':len(data),'excluded_unaligned_intervals':data.attrs['excluded_unaligned_intervals'],
                      'identical_duplicates_removed':data.attrs['identical_duplicates_removed'],
                      'conflicting_duplicate_rows_excluded':data.attrs['conflicting_duplicate_rows_excluded'],
                      'source_days':int(pd.to_datetime(data['Fecha inicial']).dt.normalize().nunique()),
                      'downloaded_at_utc':datetime.now(timezone.utc).isoformat(),
                      'validation_status':'published_quality_not_verified'}
                path.write_bytes(gzip.compress(raw,mtime=0));manifest.write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
            data=validate_export(raw,start,end,variable)
            print(f'SISAIRE {year} {variable}: {len(data):,} registros, {data.Estacion.nunique()} estaciones',flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--network',action='store_true')
    parser.add_argument('--start-year',type=int,default=2015)
    parser.add_argument('--end-year',type=int,default=2025)
    args=parser.parse_args()
    if not 2015<=args.start_year<=args.end_year<=2025:parser.error('Selecciona años de 2015–2025.')
    collect(args.root,years=range(args.start_year,args.end_year+1),network=args.network)
