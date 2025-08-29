document.addEventListener('DOMContentLoaded', () => {
    const tables = document.querySelectorAll('table');

    tables.forEach(table => {
        const tableId = table.id;
        const filterInputs = table.querySelectorAll('.filter-input');
        const sortSelects = table.querySelectorAll('.sort-select');
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));

        function filterAndSort() {
            // Filtra as linhas
            let visibleRows = rows.filter(row => {
                let match = true;
                filterInputs.forEach(input => {
                    const colIndex = input.dataset.col;
                    const filterText = input.value.toLowerCase();
                    const cellText = row.children[colIndex].textContent.toLowerCase();
                    if (filterText && !cellText.includes(filterText)) {
                        match = false;
                    }
                });
                return match;
            });

            // Ordena as linhas
            sortSelects.forEach(select => {
                const sortCol = select.dataset.col;
                const sortDir = select.value;
                const dataType = select.dataset.type;

                if (sortDir) {
                    visibleRows.sort((a, b) => {
                        const aText = a.children[sortCol].textContent.toLowerCase();
                        const bText = b.children[sortCol].textContent.toLowerCase();

                        if (dataType === 'date') {
                            const dateA = new Date(aText);
                            const dateB = new Date(bText);
                            if (dateA < dateB) return sortDir === 'desc' ? 1 : -1;
                            if (dateA > dateB) return sortDir === 'desc' ? -1 : 1;
                        } else {
                            if (aText < bText) return sortDir === 'desc' ? 1 : -1;
                            if (aText > bText) return sortDir === 'desc' ? -1 : 1;
                        }
                        return 0;
                    });
                }
            });

            // Renderiza as linhas filtradas e ordenadas
            tbody.innerHTML = '';
            visibleRows.forEach(row => tbody.appendChild(row));
        }

        filterInputs.forEach(input => input.addEventListener('input', filterAndSort));
        sortSelects.forEach(select => select.addEventListener('change', filterAndSort));
        
        filterAndSort(); // Executa ao carregar a página
    });

    // Funções de tela cheia, etc., podem permanecer aqui
    function abrirTelaCheia(idTabela) {
        var tabela = document.getElementById(idTabela);
        if (tabela.requestFullscreen) {
            tabela.requestFullscreen();
        } else if (tabela.webkitRequestFullscreen) {
            tabela.webkitRequestFullscreen();
        } else if (tabela.msRequestFullscreen) {
            tabela.msRequestFullscreen();
        }
    }
    window.abrirTelaCheia = abrirTelaCheia;
});