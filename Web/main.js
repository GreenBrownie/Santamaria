// Cargar y mostrar datos de los archivos JSON
async function cargarJSON(url) {
    try {
        const resp = await fetch(url);
        if (!resp.ok) {
            throw new Error(`HTTP error! status: ${resp.status} - ${resp.statusText}`);
        }
        const data = await resp.json();
        return data;
    } catch (error) {
        throw error;
    }
}

function renderPredicciones(data) {
    const tbody = document.getElementById('predicciones-futuras');
    if (!tbody) {
        console.error('!predicciones-futuras');
        return;
    }
    
    tbody.innerHTML = data.map(reg => `
        <tr>
            <td>${reg.fecha}</td>
            <td>${reg.id_equipo_local}</td>
            <td>${reg.id_equipo_visitante}</td>
            <td><strong>${reg.prediccion_letra}</strong></td>
            <td>${reg.porcentaje_home.toFixed(2)}%</td>
            <td>${reg.porcentaje_draw.toFixed(2)}%</td>
            <td>${reg.porcentaje_away.toFixed(2)}%</td>
        </tr>
    `).join('');
}

function renderPasados(data) {
    const tbody = document.getElementById('partidos-pasados');
    if (!tbody) {

        return;
    }
    
    tbody.innerHTML = data.map(reg => `
        <tr>
            <td>${reg.fecha}</td>
            <td>${reg.id_equipo_local}</td>
            <td>${reg.id_equipo_visitante}</td>
            <td>${reg.resultado_final}</td>
            <td>${reg.goles_local_ht.toFixed(2)}</td>
            <td>${reg.goles_visitante_ht.toFixed(2)}</td>
        </tr>
    `).join('');

}

async function main() {
    const statusDiv = document.getElementById('status');
    try {
        
        const predicciones = await cargarJSON("prediccionesFuturas.json");
        const pasados = await cargarJSON("partidosPasados.json");
        
        renderPredicciones(predicciones);
        renderPasados(pasados);
        
    } catch (error) {
        const mensaje = 'Error: ' + error.message;
        statusDiv.innerHTML = '<div class="error">' + mensaje + '</div>';
        console.error(mensaje);
        console.error('Detalles del error:', error);
    }
}

document.addEventListener('DOMContentLoaded', main);