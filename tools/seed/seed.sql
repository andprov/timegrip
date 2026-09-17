-- Test data for manual/browser testing: 1 user, 10 projects, ~3 months of
-- time entries counting back from *today* — dates are computed at load
-- time (CURRENT_DATE), not hardcoded, so "this month"/"this year" report
-- filters always have data no matter when you run this. Safe to re-run
-- any time — it deletes its own previous run first (cascades to that
-- user's projects/timers), then reinserts fresh.
--
-- Login after loading: user@example.com / Passw0rd
--
-- Load it (local dev, Postgres reachable on localhost:5432 per .env):
--   PGPASSWORD=postgres psql -h localhost -U postgres -d timegrip -f tools/seed/seed.sql
--
-- Load it against a Docker Compose deployment (no host DB port needed):
--   docker compose exec -T db psql -U postgres -d timegrip < tools/seed/seed.sql

BEGIN;

DELETE FROM app_user WHERE email = 'user@example.com';

DO $$
DECLARE
    v_user_id uuid := gen_random_uuid();
    v_names text[] := ARRAY[
        'Website Redesign', 'Mobile App', 'Marketing Campaign',
        'Internal Tools', 'Client Support', 'Data Migration',
        'API Integration', 'QA Testing', 'Research', 'DevOps'
    ];
    v_colors text[] := ARRAY[
        '#F44336', '#FF9800', '#FFEB3B', '#4CAF50', '#00CCCC',
        '#2196F3', '#3F51B5', '#9C27B0', '#E91E63', '#9E9E9E'
    ];
    v_rates numeric[] := ARRAY[
        NULL, 25, 15, NULL, 35, 20, 20, NULL, 35, NULL
    ];
    v_round_flags boolean[] := ARRAY[
        false, true, false, false, true, false, false, false, false, false
    ];
    v_project_ids uuid[] := ARRAY[]::uuid[];

    v_day date;
    v_end_date date := CURRENT_DATE - 1;
    v_cursor timestamptz;
    v_entries int;
    v_start timestamptz;
    v_end timestamptz;
    v_idx int;
    v_hourly numeric;
    v_r2h boolean;
    v_amount numeric;
    v_timer_count int := 0;
BEGIN
    INSERT INTO app_user (id, email, hashed_password, is_active, time_format)
    VALUES (
        v_user_id, 'user@example.com',
        '$2b$12$NDSKCAOVxm8gwwf4M7LTVe/oewkV4vL1N.c27Fu8X9f5vAeS5BOMy',
        true, '24h'
    );

    FOR i IN 1..10 LOOP
        v_project_ids := array_append(v_project_ids, gen_random_uuid());
        INSERT INTO app_project
            (id, name, color, hourly_rate, round_to_hour, status, user_id)
        VALUES (
            v_project_ids[i], v_names[i], v_colors[i],
            v_rates[i], v_round_flags[i], 'active', v_user_id
        );
    END LOOP;

    v_day := CURRENT_DATE - INTERVAL '3 months';
    WHILE v_day <= v_end_date LOOP
        IF EXTRACT(DOW FROM v_day) BETWEEN 1 AND 5 OR random() < 0.08 THEN
            v_cursor := (v_day + TIME '09:00') AT TIME ZONE 'UTC'
                + ((floor(random() * 61)::int - 30) || ' minutes')::interval;
            v_entries := 2 + floor(random() * 4)::int;

            FOR j IN 1..v_entries LOOP
                v_start := v_cursor;
                v_end := v_start
                    + ((25 + floor(random() * 156)::int) || ' minutes')::interval;

                EXIT WHEN (v_end AT TIME ZONE 'UTC')::date <> v_day
                    OR EXTRACT(HOUR FROM v_end AT TIME ZONE 'UTC') >= 19;

                v_idx := 1 + floor(random() * 10)::int;
                v_hourly := v_rates[v_idx];
                v_r2h := v_round_flags[v_idx];
                v_amount := CASE
                    WHEN v_hourly IS NULL THEN NULL
                    ELSE round(
                        (CASE WHEN v_r2h THEN
                            round(EXTRACT(EPOCH FROM (v_end - v_start)) / 3600.0)
                        ELSE
                            EXTRACT(EPOCH FROM (v_end - v_start)) / 3600.0
                        END) * v_hourly,
                        2
                    )
                END;

                INSERT INTO app_timer (
                    id, start_time, end_time, hourly_rate, round_to_hour,
                    billable_amount, user_id, project_id
                ) VALUES (
                    gen_random_uuid(), v_start, v_end, v_hourly, v_r2h,
                    v_amount, v_user_id, v_project_ids[v_idx]
                );
                v_timer_count := v_timer_count + 1;

                v_cursor := v_end
                    + ((5 + floor(random() * 41)::int) || ' minutes')::interval;
            END LOOP;
        END IF;
        v_day := v_day + 1;
    END LOOP;

    RAISE NOTICE 'Seeded % time entries', v_timer_count;
END $$;

COMMIT;
