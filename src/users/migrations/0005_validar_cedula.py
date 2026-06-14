from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_passwordresettoken'),
    ]

    operations = [
        migrations.RunSQL(
            sql='''
            CREATE OR REPLACE FUNCTION validar_cedula_ecuatoriana(cedula VARCHAR) RETURNS BOOLEAN AS $$
            DECLARE
                provincia INT;
                tercer_digito INT;
                suma INT := 0;
                digito INT;
                ultimo_digito INT;
                decena INT;
                multiplo INT;
                i INT;
            BEGIN
                IF LENGTH(cedula) != 10 THEN
                    RETURN FALSE;
                END IF;
                
                IF cedula !~ '^[0-9]+$' THEN
                    RETURN FALSE;
                END IF;

                provincia := CAST(SUBSTRING(cedula FROM 1 FOR 2) AS INT);
                tercer_digito := CAST(SUBSTRING(cedula FROM 3 FOR 1) AS INT);
                ultimo_digito := CAST(SUBSTRING(cedula FROM 10 FOR 1) AS INT);

                IF provincia < 1 OR provincia > 24 THEN
                    IF provincia != 30 THEN
                        RETURN FALSE;
                    END IF;
                END IF;

                IF tercer_digito > 5 THEN
                    RETURN FALSE;
                END IF;

                FOR i IN 1..9 LOOP
                    digito := CAST(SUBSTRING(cedula FROM i FOR 1) AS INT);
                    IF i % 2 = 1 THEN
                        multiplo := digito * 2;
                        IF multiplo > 9 THEN
                            multiplo := multiplo - 9;
                        END IF;
                        suma := suma + multiplo;
                    ELSE
                        suma := suma + digito;
                    END IF;
                END LOOP;

                decena := suma / 10;
                decena := (decena + 1) * 10;
                
                IF (decena - suma) = 10 THEN
                    IF ultimo_digito = 0 THEN
                        RETURN TRUE;
                    ELSE
                        RETURN FALSE;
                    END IF;
                ELSIF (decena - suma) = ultimo_digito THEN
                    RETURN TRUE;
                ELSE
                    RETURN FALSE;
                END IF;
            END;
            $$ LANGUAGE plpgsql;

            ALTER TABLE usuarios ADD CONSTRAINT cedula_valida CHECK (validar_cedula_ecuatoriana(cedula));
            ''',
            reverse_sql='''
            ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS cedula_valida;
            DROP FUNCTION IF EXISTS validar_cedula_ecuatoriana(VARCHAR);
            '''
        )
    ]
