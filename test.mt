let
    var fact1: Integer;
    var fact2: Integer;
    func abc(a:Integer, b:Integer, c:Integer):Integer
        begin
            return a+b+c;
        end
in
    begin
        getint(x);
        fact1 := abc(1,2,3);
        fact1 := fact1 + x;
        fact2 := abc(4,6,7);
        putint(fact1);
    end