import pandas as pd
from sqlalchemy import create_engine
from typing import Optional
from .config import CONFIG_BD, COLUMNAS_USAR

class CargadorDatos:
    def __init__(self, config_bd: dict = None):
        self.config_bd = config_bd or CONFIG_BD
        self.engine = None

    def conectar(self) -> bool:
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
            return True


    def desconectar(self):
        if self.engine:
            self.engine.dispose()
            self.engine = NonSe

    def cargar(self, consulta: Optional[str] = None, limite: Optional[int] = None) -> pd.DataFrame:
        #Ejecuta la consulta y devuelve un DataFrame Si no se especifica consulta, selecciona COLUMNAS_USAR
        self.conectar()

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
