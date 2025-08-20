# Reactor Simulation API

This API provides endpoints for uploading reactor simulation experiments with TSV data files and processing them asynchronously.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file with the following variables:

```env
# Database
DB_PATH=users.db

# Server Configuration
HOST=localhost
PORT=8080
DEBUG=true

# Admin User
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=your_secure_password

# Uploads Directory
UPLOADS_DIR=uploads

# Experiment Processing Configuration
TRIES_TO_FAIL_EXPERIMENT=3
EXPERIMENT_TIMEOUT_MINUTES=15
```

### 3. Start the Server

```bash
python app/app.py
```

## API Endpoints

### Authentication

All endpoints require authentication using Bearer tokens.

#### Login
```http
POST /login
Content-Type: application/json

{
    "username": "admin",
    "password": "your_secure_password"
}
```

Response:
```json
{
    "token": "your_jwt_token",
    "expires_at": "2024-01-01T12:00:00",
    "message": "Login successful"
}
```

### Reactor Experiment Endpoints

#### Upload Experiment
```http
POST /reactor/upload
Authorization: Bearer your_jwt_token
Content-Type: multipart/form-data

Form Data:
- experiment_name: "My Experiment"
- tsv_file: [TSV file]
- t_add: 7380.0 (optional)
- t_span_start: 0.0 (optional)
- t_span_end: 13100.0 (optional)
- dt: 1.0 (optional)
- f_j1: 0.05 (optional)
- f_j2: 10.0 (optional)
- L_0i: 0.25 (optional)
- CVAM_r0i: 1e-10 (optional)
- CBA_r0i: 1e-10 (optional)
- CNaPS_r0i: 0.0007 (optional)
- CTBHP_r0i: 0.00042 (optional)
- CCRD_r0i: 0.00066 (optional)
- CMPOL_r0i: 1e-10 (optional)
- Np_r0i: 1e-10 (optional)
- T1_0i: 296.15 (optional)
- T3_0i: 295.15 (optional)
```

Response:
```json
{
    "experiment_id": 1,
    "experiment_name": "My Experiment",
    "status": "pending",
    "message": "Experiment uploaded successfully and queued for processing"
}
```

#### Get User Experiments
```http
GET /reactor/experiments
Authorization: Bearer your_jwt_token
```

Response:
```json
{
    "experiments": [
        {
            "id": 1,
            "experiment_name": "My Experiment",
            "status": "completed",
            "number_of_tries": 1,
            "created_at": "2024-01-01T10:00:00",
            "started_at": "2024-01-01T10:01:00",
            "completed_at": "2024-01-01T10:02:30"
        }
    ]
}
```

#### Get Experiment Details
```http
GET /reactor/experiments/{experiment_id}
Authorization: Bearer your_jwt_token
```

Response:
```json
{
    "experiment": {
        "id": 1,
        "user_id": 1,
        "experiment_name": "My Experiment",
        "tsv_file_path": "uploads/abc123.txt",
        "status": "completed",
        "number_of_tries": 1,
        "created_at": "2024-01-01T10:00:00",
        "started_at": "2024-01-01T10:01:00",
        "completed_at": "2024-01-01T10:02:30",
        "error_message": null
    },
    "parameters": {
        "t_add": 7380.0,
        "adj_factor": [0.05, 10.0],
        "t_span": [0.0, 13100.0],
        "dt": 1.0
    },
    "results": {
        "time": [0, 1, 2, ...],
        "liquid_level": [0.25, 0.251, ...],
        "vam_concentration": [1e-10, 1.1e-10, ...],
        "ba_concentration": [1e-10, 1.1e-10, ...],
        "naps_concentration": [0.0007, 0.00069, ...],
        "tbhp_concentration": [0.00042, 0.00041, ...],
        "crd_concentration": [0.00066, 0.00065, ...],
        "polymer_concentration": [1e-10, 1.2e-10, ...],
        "particle_number": [1e-10, 1.1e-10, ...],
        "reactor_temperature": [296.15, 296.2, ...],
        "jacket_temperature": [295.15, 295.2, ...],
        "viscosity": [0.001, 0.0011, ...],
        "heat_transfer_rate": [100, 105, ...],
        "heat_transfer_coeff": [50, 52, ...]
    }
}
```

#### Get Experiment Results
```http
GET /reactor/experiments/{experiment_id}/results
Authorization: Bearer your_jwt_token
```

Response:
```json
{
    "experiment_id": 1,
    "results": {
        "time": [0, 1, 2, ...],
        "liquid_level": [0.25, 0.251, ...],
        "vam_concentration": [1e-10, 1.1e-10, ...],
        "ba_concentration": [1e-10, 1.1e-10, ...],
        "naps_concentration": [0.0007, 0.00069, ...],
        "tbhp_concentration": [0.00042, 0.00041, ...],
        "crd_concentration": [0.00066, 0.00065, ...],
        "polymer_concentration": [1e-10, 1.2e-10, ...],
        "particle_number": [1e-10, 1.1e-10, ...],
        "reactor_temperature": [296.15, 296.2, ...],
        "jacket_temperature": [295.15, 295.2, ...],
        "viscosity": [0.001, 0.0011, ...],
        "heat_transfer_rate": [100, 105, ...],
        "heat_transfer_coeff": [50, 52, ...]
    }
}
```

#### Retry Failed Experiment
```http
POST /reactor/experiments/{experiment_id}/retry
Authorization: Bearer your_jwt_token
```

Response:
```json
{
    "experiment_id": 1,
    "message": "Experiment reset to pending for retry"
}
```

## TSV File Format

The TSV file must contain the following columns:

| Column Name | Description | Units |
|-------------|-------------|-------|
| t[s] | Time | seconds |
| F2[m^3/s] | Flow rate 2 (cooling jacket) | m³/s |
| F7[m^3/s] | Flow rate 7 (monomer feed) | m³/s |
| F8[m^3/s] | Flow rate 8 (initiator feed) | m³/s |
| F9[m^3/s] | Flow rate 9 (catalyst feed) | m³/s |
| RPS[RPS] | Reactor stirring speed | RPM |
| T1[K] | Reactor temperature | Kelvin |
| T2[K] | Cooling water inlet temperature | Kelvin |
| T3[K] | Jacket temperature | Kelvin |

### Example TSV Structure:
```
t[s]    F2[m^3/s]  F7[m^3/s]  F8[m^3/s]  F9[m^3/s]  RPS[RPS]  T1[K]     T2[K]     T3[K]
0       0.001      0.001      0.001      0.001      300       296.15    293.15    295.15
1       0.001      0.001      0.001      0.001      300       296.2     293.2     295.2
2       0.001      0.001      0.001      0.001      300       296.25    293.25    295.25
...
```

## Parameters

### Time Parameters
- `t_add`: Time when feed composition changes (default: 7380.0s)
- `t_span_start`: Simulation start time (default: 0.0s)
- `t_span_end`: Simulation end time (default: 13100.0s)
- `dt`: Time step for integration (default: 1.0s)

### Adjustment Factors
- `f_j1`: Natural convection heat transfer factor (default: 0.05)
- `f_j2`: Forced convection heat transfer factor (default: 10.0)

### Initial Conditions (Optional)
- `L_0i`: Initial liquid level (m)
- `CVAM_r0i`: Initial VAM concentration (kmol/m³)
- `CBA_r0i`: Initial BA concentration (kmol/m³)
- `CNaPS_r0i`: Initial NaPS concentration (kmol/m³)
- `CTBHP_r0i`: Initial TBHP concentration (kmol/m³)
- `CCRD_r0i`: Initial CRD concentration (kmol/m³)
- `CMPOL_r0i`: Initial polymer concentration (kg/m³)
- `Np_r0i`: Initial particle number
- `T1_0i`: Initial reactor temperature (K)
- `T3_0i`: Initial jacket temperature (K)

## Cron Job Setup

To process experiments automatically, set up a cron job to run the processing script:

### 1. Make the script executable
```bash
chmod +x app/process_experiments.py
```

### 2. Add to crontab
```bash
crontab -e
```

Add one of these lines depending on your needs:
```bash
# Run every 5 minutes
*/5 * * * * cd /path/to/your/project && python app/process_experiments.py >> logs/cron.log 2>&1

# Run every minute
* * * * * cd /path/to/your/project && python app/process_experiments.py >> logs/cron.log 2>&1

# Run every 10 minutes
*/10 * * * * cd /path/to/your/project && python app/process_experiments.py >> logs/cron.log 2>&1
```

### 3. Create logs directory
```bash
mkdir logs
```

## Experiment Status

Experiments go through the following statuses:

1. **pending**: Experiment uploaded, waiting for processing
2. **running**: Currently being processed
3. **completed**: Successfully completed with results available
4. **failed**: Failed with error message (can be retried)
5. **failed_permanently**: Failed after exceeding maximum retry attempts

## Retry Mechanism

The system includes a robust retry mechanism:

### Automatic Retries
- Experiments are automatically retried when they fail
- Each failure increments the `number_of_tries` counter
- After `TRIES_TO_FAIL_EXPERIMENT` attempts, experiments are marked as `failed_permanently`

### Timeout Handling
- Experiments that run longer than `EXPERIMENT_TIMEOUT_MINUTES` are automatically reset
- Timed-out experiments are marked as `pending` and their try count is incremented
- This prevents experiments from getting stuck in `running` status

### Manual Retry
- Users can manually retry failed experiments using the `/retry` endpoint
- Permanently failed experiments cannot be retried
- Running or completed experiments cannot be retried

## Environment Variables

### Processing Configuration
- `TRIES_TO_FAIL_EXPERIMENT`: Maximum number of retry attempts (default: 3)
- `EXPERIMENT_TIMEOUT_MINUTES`: Timeout for running experiments (default: 15)

### Example Configuration
```env
# Allow 5 retry attempts
TRIES_TO_FAIL_EXPERIMENT=5

# Timeout after 20 minutes
EXPERIMENT_TIMEOUT_MINUTES=20
```

## Error Handling

- If an experiment fails, the error message is stored in the database
- Failed experiments are automatically retried up to the configured limit
- Permanently failed experiments cannot be retried
- File validation ensures only TSV files are accepted
- Required columns are validated before processing
- Timeout detection prevents experiments from getting stuck

## File Storage

- TSV files are stored in the `uploads/` directory (configurable via `UPLOADS_DIR`)
- Files are renamed with UUIDs to prevent conflicts
- Files are automatically cleaned up if database operations fail

## Security

- All endpoints require authentication
- Users can only access their own experiments
- File uploads are validated for type and content
- SQL injection is prevented through parameterized queries 