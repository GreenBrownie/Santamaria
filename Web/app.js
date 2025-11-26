// === PREDICCIONES ===
function setupPredicciones() {

  statePred.rows = predicciones.map(p => ({
    equipo_local: p.nombre_equipo_local || p.equipo_local || '',
    equipo_visitante: p.nombre_equipo_visitante || p.equipo_visitante || '',
    fecha: p.fecha,
    prediccion: p.prediccion_letra || p.prediccion,
    porcentaje_home: p.porcentaje_home,
    porcentaje_draw: p.porcentaje_draw,
    porcentaje_away: p.porcentaje_away,
    timestamp: p.timestamp_prediccion
  }));

  const cols = [
    { key: 'fecha', label: 'Fecha', sortable: true },
    { key: 'equipo_local', label: 'Local', sortable: true },
    { key: 'equipo_visitante', label: 'Visitante', sortable: true },
    { key: 'prediccion', label: 'Predicción', sortable: true },
    { key: 'porcentaje_home', label: '% Home', sortable: true },
    { key: 'porcentaje_draw', label: '% Draw', sortable: true },
    { key: 'porcentaje_away', label: '% Away', sortable: true }
  ];

  function draw() {
    const rows = applyFilters(statePred);
    const pageSize = parseInt($('#page-size-pred').value, 10) || 10;
    const page = statePred.page || 1;

    renderTable({
      containerId: '#table-pred-container',
      columns: cols,
      rows,
      page,
      pageSize,
      onSort: (key) => {
        if (statePred.sortKey === key) {
          statePred.sortDir *= -1;
        } else {
          statePred.sortKey = key;
          statePred.sortDir = 1;
        }
        draw();
      }
    });

    renderPagination('#pagination-pred', rows.length, page, pageSize, (p) => {
      statePred.page = p;
      draw();
    });
  }

  $('#search-pred').addEventListener('input', (e) => {
    statePred.filterText = e.target.value;
    statePred.page = 1;
    draw();
  });

  $('#filter-pred').addEventListener('change', (e) => {
    const v = e.target.value;
    statePred.extraFilter = v ? (r => String(r.prediccion).trim() === v) : null;
    statePred.page = 1;
    draw();
  });

  $('#page-size-pred').addEventListener('change', (e) => {
    statePred.pageSize = parseInt(e.target.value, 10);
    statePred.page = 1;
    draw();
  });

  $('#page-size-pred').value = '10';
  draw();
}
