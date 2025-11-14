import pandas as pd
from sqlalchemy import create_engine
from typing import Optional
from .config import CONFIG_BD, COLUMNAS_USAR

class CargadorDatos:
    def __init__(self, config_bd: dict = None):
        self.config_bd = config_bd or CONFIG_BD
        self.engine = None

        #Crea el engine de SQLAlchemy
        user = self.config_bd['user']
        pwd = self.config_bd['password']
        host = self.config_bd['host']
        port = self.config_bd['port']
        db   = self.config_bd['database']
        url = f"mysql+mysqlconnector://{user}:{pwd}@{host}:{port}/{db}"
        self.engine = create_engine(url, echo=False)
        #Prueba sencilla de conexión
        with self.engine.connect() as conn:
            #ta bien
            pass


    def desconectar(self):
        if self.engine:
            self.engine.dispose()
            self.engine = None

    def cargar(self, consulta: Optional[str] = None, limite: Optional[int] = None) -> pd.DataFrame:
        #Ejecuta la consulta y devuelve un DataFrame Si no se especifica consulta, selecciona COLUMNAS_USAR
        if consulta is None:
            cols = ', '.join(COLUMNAS_USAR)
            consulta = f"SELECT {cols} FROM partidosml"
            if limite:
                consulta += f" LIMIT {limite}"

        df = pd.read_sql(consulta, con=self.engine)
        return df


    def cargar_todos(self) -> pd.DataFrame:
        return self.cargar()

    def cargar_muestra(self, n: int = 100) -> pd.DataFrame:
        return self.cargar(limite=n)

    # Validar registro unico de partido, tabla como param para funcionar con la base normalizada
    def registro_unico(self, tabla: str) -> pd.DataFrame:
        query = f"SELECT id_equipo_local, id_equipo_visitante, fecha FROM {tabla}"
        return pd.read_sql(query, con=self.engine)

    def insertar_sin_duplicados(self, df: pd.DataFrame, tabla: str):
        existentes = self.registro_unico(tabla)
        if existentes.empty:
            df.to_sql(tabla, con=self.engine, if_exists='append', index=False)
            print(f"{len(df)} registros insertados en '{tabla}'.")
            return

        df['fecha'] = pd.to_datetime(df['fecha'])
        existentes['fecha'] = pd.to_datetime(existentes['fecha'])
        # Es más rapido que el and en sql?
        df['clave'] = (
            df['id_equipo_local'].astype(str) + '_' +
            df['id_equipo_visitante'].astype(str) + '_' +
            df['fecha'].dt.strftime('%Y-%m-%d')
        )
        existentes['clave'] = (
            existentes['id_equipo_local'].astype(str) + '_' +
            existentes['id_equipo_visitante'].astype(str) + '_' +
            existentes['fecha'].dt.strftime('%Y-%m-%d')
        )

        nuevos = df[~df['clave'].isin(existentes['clave'])].copy()
        nuevos.drop(columns=['clave'], inplace=True)

        if nuevos.empty:
            print("FLAG Sin registros")
            return

        nuevos.to_sql(tabla, con=self.engine, if_exists='append', index=False)
