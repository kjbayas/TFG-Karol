$(document).ready(function() {
    console.log('Entrando correctamente');
    console.log(tiene_permiso);
    console.log("Eventos mirando ", events);

    // Función para cargar y mostrar los eventos en la lista
    function loadEventList() {
        var eventList = $('#eventList');
        eventList.empty();

        var columnHeader = `
            <a href="#" class="list-group-item list-group-item-action active text-center">
                <div class="row">
                    <div class="col-md-4"><strong>Title</strong></div>
                    <div class="col-md-2"><strong>Start Date</strong></div>
                    <div class="col-md-2"><strong>End Date</strong></div>
                    <div class="col-md-2"><strong>Place or URL</strong></div>
                    <div class="col-md-2"><strong>Action</strong></div>
                </div>
            </a>`;
        eventList.append(columnHeader);

        // Ordenar los eventos por fecha de inicio
        events.sort(function(a, b) {
            var dateA = moment(a.start).toDate();
            var dateB = moment(b.start).toDate();
            return dateA - dateB;
        });

        // Filtrar eventos para mostrar solo los del día de hoy y futuros
        var today = moment().startOf('day');
        var futureEvents = events.filter(function(event) {
            return moment(event.start) >= today;
        });

        futureEvents.forEach(function(event) {
            var startFormatted = moment(event.start).format("DD/MM/YYYY HH:mm");
            var endFormatted = moment(event.end).format("DD/MM/YYYY HH:mm");
            var deleteButton = `<button class="btn btn-danger delete-event-button" data-event-id="${event.id}">Delete</button>`;
            var eventListItem = `
                <li class="list-group-item text-center">
                    <div class="row">
                        <div class="col-md-4">${event.title}</div>
                        <div class="col-md-2">${startFormatted}</div>
                        <div class="col-md-2">${endFormatted}</div>
                        <div class="col-md-2">${event.place}</div>
                        <div class="col-md-2">${deleteButton}</div>
                    </div>
                </li>`;
            eventList.append(eventListItem);
        });

        // Vincular evento click a los botones de eliminación solo si tiene_permiso es true
        if (tiene_permiso) {
            $('.delete-event-button').click(function() {
                var eventId = $(this).data('event-id');
                deleteEvent(eventId);
            });
        } else {
            // Ocultar botones de eliminación si no tiene permiso
            $('.delete-event-button').hide();
        }
    }

    // Lógica para eliminar un evento solo si tiene_permiso es true
    function deleteEvent(id) {
        if (!tiene_permiso) {
            console.log('No tiene permiso para eliminar eventos.');
            return;
        }
        $.ajax({
            url: '/ajax_delete',
            type: 'POST',
            data: { id: id },
            success: function(response) {
                if (response.status === 'success') {
                    loadEventList();
                    location.reload(); // Recargar la página después de eliminar un evento
                } else {
                    console.log('Error al eliminar el evento:', response.message);
                }
            },
            error: function(error) {
                console.log('Error en la solicitud AJAX:', error);
            }
        });
    }

    // Lógica para añadir un evento solo si tiene_permiso es true
    $('#createEventButton').click(function() {

        var title = $('#eventTitle').val();
        var place = $('#eventPlace').val();
        var start = $('#eventStart').val();
        var end = $('#eventEnd').val();
        addEvent(title, place, start, end);
    });

    function addEvent(title, place, start, end) {
        // Validar que se hayan seleccionado horas antes de crear el evento
        if (!start || !end) {
            alert("Por favor, selecciona una hora de inicio y una hora de fin para el evento.");
            return;
        }
    
        // Convertir las cadenas de fecha en objetos Date para compatibilidad con moment.js
        var startTime = moment(new Date(start), "YYYY-MM-DDTHH:mm:ss");
        var endTime = moment(new Date(end), "YYYY-MM-DDTHH:mm:ss");
    
        // Validar que start sea antes que end
        if (!startTime.isBefore(endTime)) {
            alert("La fecha de inicio debe ser anterior a la fecha de fin del evento.");
            return;
        }
    
        // Formatear fechas y horas en formato compatible con MySQL
        var formattedStart = startTime.format("YYYY-MM-DDTHH:mm:ss");
        var formattedEnd = endTime.format("YYYY-MM-DDTHH:mm:ss");
    
        $.ajax({
            url: '/insert',
            type: 'POST',
            data: { title: title, place: place, start: formattedStart, end: formattedEnd },
            success: function(response) {
                console.log('Respuesta del servidor:', response);
                if (response.status === 'success') {
                    loadEventList();
                    $('#eventTitle').val('');
                    $('#eventPlace').val('');
                    $('#eventStart').val('');
                    $('#eventEnd').val('');
                    location.reload();
                } else {
                    console.log('Error al añadir el evento:', response.message);
                }
            },
            error: function(error) {
                console.log('Error en la solicitud AJAX:', error);
            }
        });
    }

    // cargar la lista de eventos
    loadEventList();

    $('#calendar').fullCalendar({
        header: {
            left: 'prev,next today',
            center: 'title',
            right: 'month,agendaWeek,agendaDay'
        },
        eventClick: function(event) {
            $('#editEventModal').modal('show');  
            $('#editEventTitle').val(event.title);
            $('#editEventPlace').val(event.place);
            $('#editEventStart').val(moment(event.start).format("YYYY-MM-DDTHH:mm"));
            $('#editEventEnd').val(moment(event.end).format("YYYY-MM-DDTHH:mm"));
            $('#editEventId').val(event.id);
            console.log("Title:", event.title);
            console.log("Start:", moment(event.start).format("YYYY-MM-DDTHH:mm"));
        },
        events: events, 
    });

    // Lógica para editar un evento solo si tiene_permiso es true

    $('#editEventForm').submit(function(event) {
        event.preventDefault();
        if (!tiene_permiso) {
            console.log('No tiene permiso para editar eventos.');
            alert("NO TIENE PERMISOS");
            return;
        }
        var id = $('#editEventId').val();
        var title = $('#editEventTitle').val();
        var place = $('#editEventPlace').val();
        var start = $('#editEventStart').val();
        var end = $('#editEventEnd').val();
        
        // Validar y enviar los datos al servidor
        if (!start || !end) {
            alert("Por favor, selecciona una hora de inicio y una hora de fin para el evento.");
            return;
        }

        // Convertir las fechas a objetos de tipo Date para comparar
        var startDate = new Date(start);
        var endDate = new Date(end);
        var startHours = startDate.getHours();
        var startMinutes = startDate.getMinutes();
        var endHours = endDate.getHours();
        var endMinutes = endDate.getMinutes();

        // Validar que la fecha de inicio sea anterior a la fecha de fin
        if (startDate.getDate() === endDate.getDate() && (startHours > endHours || (startHours === endHours && startMinutes >= endMinutes))) {            
            alert("La hora de inicio debe ser anterior a la hora de fin del evento.");
            return;
        } else if (startDate > endDate) {
            alert("La fecha de inicio debe ser anterior a la fecha de fin del evento.");
            return;
        }

        $.ajax({
            url: '/update',
            type: 'POST',
            data: { id: id, title: title, place: place, start: start, end: end },
            success: function(response) {
                if (response.status === 'success') {
                    $('#editEventModal').modal('hide');
                    loadEventList();
                    location.reload();
                } else {
                    console.log('Error al actualizar el evento. Respuesta del servidor:', response);
                }
            },
            error: function(error) {
                console.log('Error en la solicitud AJAX:', error);
            }
        });
    });
    
    // cargar la lista de eventos
    loadEventList();

    $('#goBackButton').click(function() {
        console.log('Botón retroceder clicado');
        window.history.back();
    });
});
