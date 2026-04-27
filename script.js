let currentFlight = null;
let currentSeat = null;

function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
}

async function searchFlights() {
    const source = document.getElementById('src').value;
    const destination = document.getElementById('dest').value;
    
    const res = await fetch('/api/search', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ source, destination })
    });
    
    const flights = await res.json();
    const container = document.getElementById('flight-results');
    container.innerHTML = '';

    if(flights.length === 0) {
        container.innerHTML = "<p>No flights found for this route.</p>";
        return;
    }

    flights.forEach(f => {
        container.innerHTML += `
            <div class="flight-row">
                <strong>${f.airline}</strong>
                <div>${f.departure_time} → ${f.arrival_time}</div>
                <div>Stops: ${f.stops} | ${f.duration}</div>
                <strong style="color:#1a73e8">$${f.price}</strong>
                <!-- Pass airline name too so we can show it on the ticket -->
                <button class="btn-primary" onclick="loadSeats(${f.id}, ${f.price}, '${f.airline}')">Select</button>
            </div>
        `;
    });
}

async function loadSeats(flightId, price, airlineName) {
    currentFlight = { id: flightId, price: price, airline: airlineName };
    const res = await fetch(`/api/seats/${flightId}`);
    const seats = await res.json();
    
    const container = document.getElementById('seat-container');
    container.innerHTML = '';
    
    seats.forEach(s => {
        const div = document.createElement('div');
        div.className = `seat ${s.is_booked ? 'booked' : 'available'}`;
        div.innerText = s.seat_number;
        if(!s.is_booked) {
            div.onclick = () => {
                document.querySelectorAll('.seat').forEach(el => el.classList.remove('selected'));
                div.classList.add('selected');
                currentSeat = s;
                document.getElementById('btn-proceed').style.display = 'inline-block';
            };
        }
        container.appendChild(div);
    });
    showScreen('step-seats');
}

async function proceedToPayment() {
    try {
        const res = await fetch('/api/book', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                flight_id: currentFlight.id,
                seat_id: currentSeat.seat_id,
                amount: currentFlight.price
            })
        });

        const data = await res.json();

        if(data.status === 'success') {
            // FILL IN TICKET DETAILS
            document.getElementById('t-id').innerText = `#${data.booking_id}`;
            document.getElementById('t-seat').innerText = currentSeat.seat_number;
            document.getElementById('t-src').innerText = document.getElementById('src').value.toUpperCase();
            document.getElementById('t-dest').innerText = document.getElementById('dest').value.toUpperCase();
            document.getElementById('t-airline').innerText = currentFlight.airline;

            // SHOW THE CONFIRMATION SCREEN
            showScreen('step-confirm');
        } else {
            alert("Error: " + data.message);
        }
    } catch (err) {
        console.error(err);
        alert("Booking failed. Check console for details.");
    }
}