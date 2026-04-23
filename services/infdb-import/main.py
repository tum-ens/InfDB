import multiprocessing as mp
from typing import Callable, List

from infdb import InfDB

from src import (
    basemap,
    bkg,
    census2022,
    gebaeude_neuburg,
    kwp_nrw,
    kwp_nrw_oberhausen,
    lod2,
    need,
    nrw_opencloud,
    opendata_bavaria,
    openmeteo,
    plz,
    tabula,
    utils,
    waermeatlas_hessen_bensheim,
    # wetterdienst,
)

# ============================== Entry Point ============================


def _run_loader(load_fn: Callable[[InfDB], None]) -> None:
    infdb = InfDB(tool_name="infdb-import", config_path="../configs/config-infdb-import.yml")
    try:
        load_fn(infdb)
    except Exception as e:
        # Log the exception before cleanup
        try:
            log = infdb.get_logger()
            log.error(f"Error in {load_fn.__name__}: {e}", exc_info=True)
        except Exception:
            pass
        raise
    finally:
        # Ensure proper cleanup to prevent semaphore leaks
        try:
            infdb.stop_logger()
        except Exception:
            pass
        # Force garbage collection to clean up any remaining references
        import gc

        gc.collect()


def main() -> None:
    """Bootstraps loader, drops dev schema, and spawns data-loading processes.

    Behavior preserved:
    - Uses InfDB for config and centralized logging (queue listener).
    - Optionally downloads the 'opendata' package when active.
    - Drops schema 'opendata' for clean development runs.
    - Launches the original set of processes; respects utils.if_multiprocesing() to serialize.
    - Stops the queue listener at the end.
    """

    # Bootstrap InfDB (provides package config + central logging)
    infdb = InfDB(tool_name="infdb-import", config_path="../configs/config-infdb-import.yml")

    # Root logger and the running QueueListener (started by InfdbLogger internally)
    log = infdb.get_logger()

    log.info("Starting loader.............................................")
    log.info("-------------------------------------------------------------")
    log.info("-------------------------------------------------------------")

    # Download opendata package for development directly (original guard)
    # if utils.if_active("package", infdb):00
    #     package.load(infdb)

    # Drop schema "opendata" and "tmp_bld" for clean development runs
    log.info("Terminating other connections to avoid deadlocks during schema drop...")
    with infdb.connect() as db:
        db.execute_query("""SELECT pg_terminate_backend(pid)
                            FROM pg_stat_activity
                            WHERE pid <> pg_backend_pid() ;""")

    log.info("Dropping schemas for clean development run...")
    with infdb.connect() as db:  # InfdbClient context
        db.execute_query("DROP SCHEMA IF EXISTS opendata CASCADE;")
        db.execute_query("DROP SCHEMA IF EXISTS tmp_bld CASCADE;")

    # Run sql script to create changelog table and function
    log.info("Setting up changelog table and function...")
    with infdb.connect() as db:
        db.execute_sql_file("sql/changelog.sql")

    # Ensure that administrative areas are loaded for scope
    bkg.load(infdb)

    utils.create_table_building(infdb=infdb)

    # Launch data loading in parallel
    mp.freeze_support()
    processes: List[mp.Process] = []
    processes.append(mp.Process(target=_run_loader, args=(need.load,), name="need"))
    processes.append(mp.Process(target=_run_loader, args=(tabula.load,), name="tabula"))
    processes.append(mp.Process(target=_run_loader, args=(plz.load,), name="plz"))
    processes.append(mp.Process(target=_run_loader, args=(basemap.load,), name="basemap"))
    processes.append(mp.Process(target=_run_loader, args=(census2022.load,), name="census2022"))
    processes.append(mp.Process(target=_run_loader, args=(openmeteo.load,), name="openmeteo"))
    processes.append(mp.Process(target=_run_loader, args=(kwp_nrw.load,), name="kwp_nrw"))
    processes.append(mp.Process(target=_run_loader, args=(kwp_nrw_oberhausen.load,), name="kwp_nrw_oberhausen"))
    processes.append(mp.Process(target=_run_loader, args=(gebaeude_neuburg.load,), name="gebaeude-neuburg"))
    processes.append(
        mp.Process(target=_run_loader, args=(waermeatlas_hessen_bensheim.load,), name="waermeatlas_hessen_bensheim")
    )
    # processes.append(mp.Process(target=_run_loader, args=(wetterdienst.load,), name="wetterdienst"))
    processes.append(mp.Process(target=_run_loader, args=(nrw_opencloud.load,), name="nrw_opencloud"))
    processes.append(mp.Process(target=_run_loader, args=(opendata_bavaria.load,), name="opendata_bavaria"))
    processes.append(mp.Process(target=_run_loader, args=(lod2.load,), name="lod2"))

    for process in processes:
        process.start()
        if not utils.if_multiprocesing(infdb):
            process.join()
            log.info("Process %s done", process.name)
    log.info("Processes started")

    # Wait for all processes to finish and collect status
    process_results = []
    for cnt, process in enumerate(processes, 1):
        process.join()
        exitcode = process.exitcode
        status = "OK" if exitcode == 0 else "FAILED"
        log.info("Process %s done (%d out of %d) - status: %s", process.name, cnt, len(processes), status)
        process_results.append((process.name, exitcode))
        # Explicitly close the process to release resources
        process.close()

    # Create building surface tables for BY and NRW
    utils.create_building_surface_table(infdb=infdb)

    # Create building view
    utils.create_table_building_view(infdb=infdb)

    # Summarize successes and failures using stored results
    successful = [name for name, exitcode in process_results if exitcode == 0]
    failed = [name for name, exitcode in process_results if exitcode != 0]

    if successful:
        log.info("Successful processes (%d/%d): %s", len(successful), len(processes), ", ".join(successful))
    else:
        log.warning("No processes completed successfully.")

    if failed:
        log.error("Failed processes (%d/%d): %s", len(failed), len(processes), ", ".join(failed))
    else:
        log.info("No processes failed.")

    # Stop the central listener explicitly
    log.info("Processes done")
    infdb.stop_logger()

    # Clean up remaining multiprocessing resources
    import gc

    gc.collect()

    # Give time for cleanup to complete
    import time

    time.sleep(0.1)


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    mp.freeze_support()
    main()
