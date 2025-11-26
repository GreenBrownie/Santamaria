import pandas as pd
from sqlalchemy import create_engine
from typing import Optional
from .config import CONFIG_BD, COLUMNAS_USAR
from sqlalchemy import text

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

    def insertar_sin_duplicados(self, df: pd.DataFrame, tabla: str):

        # Cargar registros existentes
        query = f"""
            SELECT id_equipo_local, id_equipo_visitante, fecha, resultado_final
            FROM {tabla}
        """
        existentes = pd.read_sql(query, con=self.engine)

        # Si tabla vacía → insertar todo
        if existentes.empty:
            df.to_sql(tabla, con=self.engine, if_exists='append', index=False)
            print(f"{len(df)} registros insertados en '{tabla}'. (tabla original vacía)")
            return

        # Normalizar fechas
        df['fecha'] = pd.to_datetime(df['fecha'])
        existentes['fecha'] = pd.to_datetime(existentes['fecha'])

        # Crear clave única
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

        #Registros nuevos a insertar
        nuevos = df[~df['clave'].isin(existentes['clave'])].copy()

        if not nuevos.empty:
            nuevos.drop(columns=['clave'], inplace=True)
            nuevos.to_sql(tabla, con=self.engine, if_exists='append', index=False)
            print(f"{len(nuevos)} registros nuevos insertados en '{tabla}'.")

        # Acutaliza registros existentes con NULL en resultado_final
        # Obtener claves donde el existente tiene resultado_final NULL
        nulos = existentes[existentes['resultado_final'].isna()]['clave']

        # Filtrar solo los que tenemos en DF y están en NULL en la base
        actualizables = df[df['clave'].isin(nulos)].copy()

        if actualizables.empty:
            return

        # Ejecutar UPDATE por cada registro con NULL
        with self.engine.begin() as conn:
            for _, row in actualizables.iterrows():
                stmt = text(f"""
                    UPDATE {tabla}
                    SET resultado_final = :resultado_final
                    WHERE id_equipo_local = :local
                    AND id_equipo_visitante = :visitante
                    AND fecha = :fecha
                """)
                conn.execute(stmt, {
                    'resultado_final': row['resultado_final'],
                    'local': row['id_equipo_local'],
                    'visitante': row['id_equipo_visitante'],
                    'fecha': row['fecha']
                })

        print(f"{len(actualizables)} registros de partidos ocurridos,atualizados")

