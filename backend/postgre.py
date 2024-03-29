from psycopg.types.range import Range, RangeInfo, register_range

conn.execute("CREATE TYPE timerange AS RANGE (SUBTYPE = text)")
info = RangeInfo.fetch(conn, "timerange")
register_range(info, conn)