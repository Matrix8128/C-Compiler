int main()
{
	int d;
	d = 0;
	int i,j;
	for(i = 0 ; i < 3; i ++)
	{
		for(j = 0 ; j < 3 ; j ++)
		{
			d = d + i*j;
		}
	}
	printf("d is %d \n",d);
	return 0;
}

