DELETE FROM box_loading_log;
UPDATE cargo_requirements 
SET boxes_loaded = 0, status = 'ASSIGNED'
WHERE soldier_id = 'SLD-1234';