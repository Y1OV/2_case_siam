import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import ast
import asyncio
import aiofiles
import aiofiles.os
import random

st.set_page_config(page_title="Анализ давления", layout="wide", page_icon="📈")

async def read_pressure_data(file_path):
    """Асинхронно считывает данные давления из файла."""
    async with aiofiles.open(file_path, mode='r', encoding='utf-8') as file:
        content = await file.readlines()
    
    data = [line.strip().split('\t') for line in content]
    df = pd.DataFrame(data, columns=['Время (часы)', 'Давление (атм)'])
    df = df.astype({'Время (часы)': float, 'Давление (атм)': float})
    return df

async def plot_pressure_data(time, pressure, mark_points, recovery_intervals, drop_intervals):
    """Создает график давления."""
    fig, ax1 = plt.subplots(figsize=(6, 4))
    ax1.plot(time, pressure, label='Pressure', color='blue')
    ax1.set_xlabel('Время (часы)')
    ax1.set_ylabel('Давление (атм)', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    
    if mark_points:
        for mark in mark_points:
            ax1.axvline(mark, color='grey', linestyle='--', alpha=0.7)
        ax1.axvline(mark_points[0], color='grey', linestyle='--', alpha=0.7, label='Trend Change')
    
    recovery_plotted = False
    drop_plotted = False
    
    for start, end in recovery_intervals:
        ax1.axvspan(start, end, color='green', alpha=0.3, label='Recovery' if not recovery_plotted else "")
        recovery_plotted = True
    
    for start, end in drop_intervals:
        ax1.axvspan(start, end, color='red', alpha=0.3, label='Drop' if not drop_plotted else "")
        drop_plotted = True
    
    ax1.legend()
    return fig

st.title("Анализ данных давления")

df_path = 'markup.csv'
data_r_path = 'data_r'

async def process_files():
    if not (await aiofiles.os.path.exists(df_path)) or not (await aiofiles.os.path.isdir(data_r_path)):
        st.error("Некорректные пути к файлам или директории.")
        return
    
    df = pd.read_csv(df_path, sep=';')
    df = df.sample(9) if len(df) > 9 else df
    cols = st.columns(3)
    
    tasks = []
    
    for i, (index, row) in enumerate(df.iterrows()):
        file_path = os.path.join(data_r_path, row['file'])
        if await aiofiles.os.path.exists(file_path):
            tasks.append((i, row, file_path, cols[i % 3]))
        else:
            st.warning(f"Файл {row['file']} не найден.")
    
    async def process_task(i, row, file_path, col):
        data = await read_pressure_data(file_path)
        time, pressure = data['Время (часы)'], data['Давление (атм)']
        
        mark_points = ast.literal_eval(row['mark']) if isinstance(row['mark'], str) else []
        recovery_intervals = ast.literal_eval(row['recovery']) if isinstance(row['recovery'], str) else []
        drop_intervals = ast.literal_eval(row['drop']) if isinstance(row['drop'], str) else []
        
        fig = await plot_pressure_data(time, pressure, mark_points, recovery_intervals, drop_intervals)
        with col:
            st.markdown(f"### Файл: {row['file']}")
            st.pyplot(fig)
    
    await asyncio.gather(*(process_task(*task) for task in tasks))

if st.button("Загрузить и построить графики"):
    asyncio.run(process_files())





