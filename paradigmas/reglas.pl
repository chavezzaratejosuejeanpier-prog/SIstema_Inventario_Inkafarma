

















:- dynamic medicamento/2.        
:- dynamic lote/4.               






vencido(LoteID) :-
    lote(LoteID, _MedID, _Cant, Dias),
    Dias < 0.


proximo_a_vencer(LoteID) :-
    lote(LoteID, _MedID, _Cant, Dias),
    Dias >= 0,
    Dias =< 30.


stock_vigente(MedID, Total) :-
    findall(Cant, (lote(_L, MedID, Cant, Dias), Dias >= 0), Cantidades),
    sum_list(Cantidades, Total).



stock_bajo(MedID) :-
    medicamento(MedID, Minimo),
    stock_vigente(MedID, Total),
    Total =< Minimo.




requiere_reposicion_urgente(MedID) :-
    stock_bajo(MedID).




requiere_retiro(LoteID) :-
    vencido(LoteID),
    lote(LoteID, _MedID, Cant, _Dias),
    Cant > 0.



alerta_critica(MedID) :-
    stock_bajo(MedID),
    lote(_L, MedID, _Cant, Dias),
    Dias >= 0,
    Dias =< 30.
