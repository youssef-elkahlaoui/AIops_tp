##### In SQL, DECLARE, BEGIN, END, COMMIT, ROLLBACK, and exception handling mechanisms are used to control the flow of execution and manage transactions.



## 1\. DECLARE:

The DECLARE statement is used to define variables or cursors within a stored procedure, function, or a SQL batch. This allows for temporary storage of data or iteration through result sets.

Code



DECLARE @myVariable INT;

DECLARE myCursor CURSOR FOR SELECT column\_name FROM table\_name;

## 2\. BEGIN and END:

BEGIN and END define a block of SQL statements. These blocks are often used with control-of-flow statements like IF, WHILE, or within a transaction to group multiple statements together.

Code



BEGIN

&nbsp;   -- SQL statements here

&nbsp;   SELECT \* FROM Employees;

&nbsp;   UPDATE Orders SET Status = 'Shipped' WHERE OrderID = 123;

END;

## 3\. Transactions (BEGIN TRANSACTION, COMMIT, ROLLBACK):

Transactions ensure data integrity by treating a series of operations as a single, atomic unit.

BEGIN TRANSACTION / START TRANSACTION: Initiates a transaction, marking the point from which changes can be committed or rolled back.

Code



&nbsp;   BEGIN TRANSACTION;

COMMIT TRANSACTION / COMMIT WORK: Permanently saves all changes made within the current transaction to the database. Once committed, changes cannot be rolled back.

Code



&nbsp;   COMMIT TRANSACTION;

ROLLBACK TRANSACTION / ROLLBACK WORK: Undoes all changes made within the current transaction, restoring the database to its state before the transaction began.

Code



ROLLBACK TRANSACTION;

## 4\. Exception Handling (TRY...CATCH in SQL Server, EXCEPTION in PL/SQL):

Exception handling allows you to manage errors that occur during the execution of SQL code, preventing the entire batch or transaction from failing unexpectedly. SQL Server (TRY...CATCH).

Code



&nbsp;   BEGIN TRY

&nbsp;       -- SQL statements that might cause an error

&nbsp;       INSERT INTO MyTable (ID) VALUES (1);

&nbsp;       INSERT INTO MyTable (ID) VALUES (1); -- This will cause a primary key violation

&nbsp;       COMMIT TRANSACTION;

&nbsp;   END TRY

&nbsp;   BEGIN CATCH

&nbsp;       -- Error handling logic

&nbsp;       SELECT ERROR\_NUMBER() AS ErrorNumber, ERROR\_MESSAGE() AS ErrorMessage;

&nbsp;       IF @@TRANCOUNT > 0

&nbsp;           ROLLBACK TRANSACTION; -- Rollback if an open transaction exists

&nbsp;   END CATCH;

## PL/SQL (EXCEPTION).

Code



&nbsp;   DECLARE

&nbsp;       v\_value NUMBER;

&nbsp;   BEGIN

&nbsp;       SELECT column\_name INTO v\_value FROM non\_existent\_table; -- This will cause an error

&nbsp;   EXCEPTION

&nbsp;       WHEN NO\_DATA\_FOUND THEN

&nbsp;           DBMS\_OUTPUT.PUT\_LINE('No data found!');

&nbsp;       WHEN OTHERS THEN

&nbsp;           DBMS\_OUTPUT.PUT\_LINE('An unexpected error occurred: ' || SQLERRM);

&nbsp;   END

