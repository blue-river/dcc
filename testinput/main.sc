const byte iets = 5;

byte counter = 20;
internal byte baz = 10;

addr byte foo = 0xFE00;
addr internal byte bar = 0xFE;

void main()
{
	interrupts.enable();

	foo.main();
	sfr.ACC = iets;

	boolean.comparisons(42 | ~0x20 & 0b1010);

	counter = 0;

	while (counter != 250)
	{
		counter = counter + 1;
	}

	if (true == false)
	{
	}
	else if (false != true)
	{
	}
	else
	{
		foo += 23;
		foo -= 23;
		foo *= 1;
		foo &= 0xFF;
		foo |= 0x00;
	}
}
