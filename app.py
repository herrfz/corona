import time
import pandas as pd
import numpy as np
import holoviews as hv
from holoviews import opts
from threading import Thread
hv.extension('bokeh')


def transform(df):
    df = df.set_index(['Province/State', 'Country/Region']).drop(columns=['Lat', 'Long']).T.rename_axis('date')
    df.index = pd.to_datetime(df.index)
    return df


def plot_country_growth_rates(country):
    confirmed_country = confirmed.loc[:, (slice(None), country)].sum(axis=1)
    confirmed_country_rate = (((confirmed_country / confirmed_country.shift() - 1) * 100)
                                  .replace([np.inf, -np.inf], np.nan).dropna())
    return (hv.Bars([(i, confirmed_country_rate.loc[i]) for i in confirmed_country_rate.index])
                .redim(x='Days', y='Daily growth rate (%)')
                .opts(height=400, width=700, fontsize={'xticks': 6},
                      xrotation=90, ylim=(0, 200), title='Day-over-Day Growth of Confirmed Cases',
                      tools=['hover'], show_frame=False))

                      
def plot_confirmed_with_recovered(country):
    confirmed_country = confirmed.loc[:, (slice(None), country)].sum(axis=1)
    recovered_country = recovered.loc[:, (slice(None), country)].sum(axis=1)
    return ((hv.Curve([(i, confirmed_country.loc[i]) for i in confirmed_country.index]) *
            hv.Curve([(i, recovered_country.loc[i]) for i in recovered_country.index]))
                .redim(x='Date', y='Number of Cases')
                .opts(opts.Curve(height=400, width=700,
                      ylim=(0, 500000), title='Confirmed and Recovered Cases',
                      show_frame=False, tools=['hover'])))


def plot_country_recovery_rates(country):
    recovered_country = recovered.loc[:, (slice(None), country)].sum(axis=1)
    recovered_country_rate = (((recovered_country / recovered_country.shift() - 1) * 100)
                                  .replace([np.inf, -np.inf], np.nan).dropna())
    return (hv.Bars([(i, recovered_country_rate.loc[i]) for i in recovered_country_rate.index])
                .redim(x='Days', y='Daily growth rate (%)')
                .opts(height=400, width=700, fontsize={'xticks': 6},
                      xrotation=90, ylim=(0, 200), title='Day-over-Day Growth of Recovered Cases',
                      tools=['hover'], show_frame=False))


def plot_current_vs_new(country):
    confirmed_country = confirmed.loc[:, (slice(None), country)].sum(axis=1)
    confirmed_country_new = confirmed_country.diff()
    return (hv.Scatter((confirmed_country, confirmed_country_new))
                .redim(x='Current cases', y='New cases')
                .opts(height=400, width=700, size=7,
                      logx=True, logy=True, xlim=(1, 1e6), ylim=(1e-1, 1e5), title='Number of Confirmed vs New Cases',
                      tools=['hover'], show_frame=False))


def plot_death_rate(country):
    confirmed_country = confirmed.loc[:, (slice(None), country)].sum(axis=1)
    recovered_country = recovered.loc[:, (slice(None), country)].sum(axis=1)
    death_country = death.loc[:, (slice(None), country)].sum(axis=1)
    death_country_rate = (death_country / (confirmed_country + recovered_country + death_country) * 100).replace([np.inf, -np.inf], np.nan).dropna()
    return (hv.Bars([(i, death_country_rate.loc[i]) for i in death_country_rate.index])
                .redim(x='Days', y='Daily rate (%)')
                .opts(height=400, width=700, fontsize={'xticks': 6},
                      xrotation=90, ylim=(0, 10), title='Daily Death Rates',
                      tools=['hover'], show_frame=False))


def plot_deaths(country):
    death_country = death.loc[:, (slice(None), country)].sum(axis=1)
    return (hv.Curve([(i, death_country.loc[i]) for i in death_country.index])
                .redim(x='Date', y='Number of Cases')
                .opts(height=400, width=700,
                      ylim=(0, 20000), title='Number of Death Cases',
                      tools=['hover'], show_frame=False))


def update():
    while True:
        global confirmed, recovered, death
        confirmed = transform(pd.read_csv(urls['confirmed']))
        recovered = transform(pd.read_csv(urls['recovered']))
        death = transform(pd.read_csv(urls['death']))
        time.sleep(3600)


urls = {'confirmed': 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv',
        'recovered': 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv',
        'death': 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'}

confirmed = pd.DataFrame()
recovered = pd.DataFrame()
death = pd.DataFrame()

thread = Thread(target=update, daemon=True)
thread.start()
time.sleep(5)  # FIXME: allow dataframes to be updated

countries = ['Germany', 'Italy', 'France', 'Spain', 'US', 'Indonesia', 'Korea, South', 'Singapore'] 

dmaps = [hv.DynamicMap(x, kdims='country').redim.values(country=countries)
            for x in [plot_country_growth_rates,
                      plot_country_recovery_rates,
                      plot_current_vs_new,
                      plot_confirmed_with_recovered,
                      plot_deaths,
                      plot_death_rate]]

layout = hv.Layout(dmaps).opts('Curve', axiswise=True).cols(2)

renderer = hv.renderer('bokeh')
doc = renderer.server_doc(layout)
doc.title = 'Covid-19 Statistics'